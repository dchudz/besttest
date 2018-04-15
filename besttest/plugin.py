import copy
import pytest
from pytest_cov.plugin import CovPlugin
from pytest_cov.engine import Central
import coverage
import re


def pytest_addoption(parser):
    """Add options to control coverage."""
    group = parser.getgroup(
        'cov', 'coverage reporting with distributed testing support')
    group.addoption('--cov-besttest', action='append', default=[],
                    metavar='path',
                    nargs='?', const=True, dest='cov_source_besttest',
                    help='measure coverage for filesystem path '
                         '(multi-allowed)')


class BestTestCovController(Central):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # will map test names to lines covered, represented as a tuple (file, line)
        self.each_test_lines_covered = {}

        # there's got to be a better way to know which failed, but I'm going
        # to do it by adding them to this set as they fail
        self.failed = set()

    def start_one(self, suffix):
        self.cov.stop()
        self.cov.save()

        self.cov = coverage.coverage(source=self.cov_source,
                                     branch=self.cov_branch,
                                     config_file=self.cov_config,
                                     data_suffix=suffix)
        self.cov.start()

    def stop_one(self, nodeid):
        data = self.cov.get_data()
        self.cov.stop()
        covered = {(file, line)
                   for file in data.measured_files()
                   for line in data.lines(file)}
        self.each_test_lines_covered[nodeid] = covered

        self.cov.save()


class BestTestCovPlugin(CovPlugin):
    def start(self, controller_cls, config=None, nodeid=None):
        super().start(controller_cls=BestTestCovController)

    @pytest.hookimpl(tryfirst=True, hookwrapper=True)
    def pytest_runtest_makereport(self):
        # execute all other hooks to obtain the report object
        outcome = yield
        rep = outcome.get_result()
        if not rep.passed:
            self.cov_controller.failed.add(rep.nodeid)

    def pytest_runtest_logstart(self, nodeid, location):
        self.cov_controller.start_one(
            # this goes in a filename, so make it a valid one
            suffix=re.sub(r'[^0-9a-zA-Z]+', '_', nodeid))

    def pytest_runtest_logfinish(self, nodeid, location):
        self.cov_controller.stop_one(nodeid)

    @pytest.hookimpl(hookwrapper=True, tryfirst=True)
    def pytest_sessionfinish(self, session, exitstatus):
        yield
        failed_tests = self.cov_controller.failed
        each_test_lines_covered = self.cov_controller.each_test_lines_covered

        def better_failure_exists(nodeid, each_test_lines_covered):
            our_lines = each_test_lines_covered[nodeid]
            return any(other_lines < our_lines
                       for other_nodeid, other_lines in
                       each_test_lines_covered.items()
                       if other_nodeid in failed_tests)

        best_failures = [
            failed for failed in failed_tests
            if not better_failure_exists(failed, each_test_lines_covered)
        ]
        if best_failures:
            message = 'All other failures include the code covered by these ' \
                      'failures: \n  %s\n' % '\n  '.join(best_failures)
            self.terminalreporter.write(message)

    def pytest_terminal_summary(self, terminalreporter):
        # hack since I don't know how to access terminalreporter in
        # pytest_sessionfinish otherwise
        self.terminalreporter = terminalreporter
        return super().pytest_terminal_summary(terminalreporter)


@pytest.mark.tryfirst
def pytest_load_initial_conftests(early_config, parser, args):
    if early_config.known_args_namespace.cov_source_besttest:
        namespace = copy.deepcopy(early_config.known_args_namespace)
        namespace.cov_source = \
            early_config.known_args_namespace.cov_source_besttest
        plugin = BestTestCovPlugin(namespace, early_config.pluginmanager)
        early_config.pluginmanager.register(plugin, '_cov')
