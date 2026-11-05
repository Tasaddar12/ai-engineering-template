"""Parse-only verification contracts; fixture commands are never executed."""
try:
    from .test_engineer_runtime import RuntimeCase
except ImportError:
    from test_engineer_runtime import RuntimeCase


def task(files, verify):
    return '<task><name>Verify boundary</name><files>' + files + '</files><verify>' + verify + '</verify></task>'


class VerifyCommandContracts(RuntimeCase):
    def test_empty_or_unclosed_automated_element_does_not_hide_a_command(self):
        directory = self.phase()
        for verify in ('<automated></automated>', '<automated>python tests/hidden.py',
                       '<automated>python tests/first.py</automated><automated>python tests/hidden.py'):
            with self.subTest(verify=verify):
                path = self.plan(directory, task('', verify))
                for verb in ('check.verify-command-paths', 'check.verify-failure-directions'):
                    self.cli(verb, '--plan', path, status=1, raw=True)

    def test_nested_failure_prose_is_not_a_command_path_or_failure_direction(self):
        directory = self.phase()
        self.put('tests/existing.py', '# Parser operand only; never execute\n')
        path = self.plan(directory, task('src/current.py', '''
<automated>python tests/existing.py</automated>
<fails_when>network/active-port, per-record/source, stale/latest/replay/provenance; remediation must not use || true.</fails_when>
'''))
        self.assertTrue(self.cli('check.verify-command-paths', '--plan', path)['valid'])
        self.assertTrue(self.cli('check.verify-failure-directions', '--plan', path)['valid'])

    def test_all_six_automated_elements_check_real_missing_operands(self):
        directory = self.phase()
        for index in range(6):
            self.put(f'tests/check{index}.py', '# Parser fixture only\n')
        for missing in range(6):
            with self.subTest(missing_element=missing):
                commands = '\n'.join('<automated>python tests/' + (f'missing{index}' if index == missing else f'check{index}') +
                                     '.py</automated><fails_when>deadline/resource and passed/measured failures</fails_when>'
                                     for index in range(6))
                path = self.plan(directory, task('', commands))
                packet = self.cli('check.verify-command-paths', '--plan', path, status=1)
                self.assertEqual([f'tests/missing{missing}.py'], [f['path'] for f in packet['findings']])

    def test_current_prior_creation_allowed_and_future_creation_rejected(self):
        directory = self.phase()
        path = self.plan(directory, task('tests/prior.py', '<automated>python tests/prior.py</automated>') +
                         task('tests/current.py', '<automated>python tests/prior.py</automated>\n'
                              '<automated>python tests/current.py</automated>'))
        self.assertTrue(self.cli('check.verify-command-paths', '--plan', path)['valid'])
        path = self.plan(directory, task('', '<automated>python tests/future.py</automated>') +
                         task('tests/future.py', '<automated>python tests/future.py</automated>'))
        packet = self.cli('check.verify-command-paths', '--plan', path, status=1)
        self.assertEqual([(1, 'tests/future.py')], [(f['task'], f['path']) for f in packet['findings']])

    def test_each_automated_element_retains_failure_direction_enforcement(self):
        directory = self.phase()
        for index in range(6):
            with self.subTest(swallowed_element=index):
                commands = '\n'.join('<automated>python tests/check.py' + (' || true' if element == index else '') +
                                     '</automated>' for element in range(6))
                path = self.plan(directory, task('', commands))
                packet = self.cli('check.verify-failure-directions', '--plan', path, status=1)
                self.assertEqual(1, len(packet['findings']))
                self.assertIn('failure is swallowed', packet['findings'][0]['reasons'])
        for command, reason in [('printf okay', 'command only prints text'),
                                ('grep expected tests/check.py', 'grep must use a quiet assertion with explicit failure direction')]:
            with self.subTest(command=command):
                path = self.plan(directory, task('', '<automated>python tests/check.py</automated>' +
                                      '<automated>' + command + '</automated>'))
                self.assertIn(reason, self.cli('check.verify-failure-directions', '--plan', path,
                                              status=1)['findings'][0]['reasons'])

    def test_legacy_plain_verify_command_behavior_remains(self):
        directory = self.phase()
        path = self.plan(directory, task('tests/current.py', 'python tests/current.py'))
        self.assertTrue(self.cli('check.verify-command-paths', '--plan', path)['valid'])
        self.assertTrue(self.cli('check.verify-failure-directions', '--plan', path)['valid'])
        path = self.plan(directory, task('', 'python tests/absent.py'))
        self.assertEqual('tests/absent.py', self.cli('check.verify-command-paths', '--plan', path,
                                                  status=1)['findings'][0]['path'])
        path = self.plan(directory, task('', 'python tests/absent.py || true'))
        self.assertFalse(self.cli('check.verify-failure-directions', '--plan', path, status=1)['valid'])
