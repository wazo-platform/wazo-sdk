import mock
import unittest
import xivoswap


class TestXiVOSwap(unittest.TestCase):
    def test_start_no_args(self):
        args = []

        parser = self._mock_parser(source_is_git=False, modules=[])
        module_swapper = mock.Mock()
        xivo_swapper = xivoswap.XiVOSwapper(parser, module_swapper)

        self.assertRaises(xivoswap.BadArgumentsException,
                          xivo_swapper.start,
                          args)

    def test_start_no_module(self):
        args = ['-g']
        parser = self._mock_parser(source_is_git=True, modules=[])
        module_swapper = mock.Mock()
        xivo_swapper = xivoswap.XiVOSwapper(parser, module_swapper)

        self.assertRaises(xivoswap.BadArgumentsException,
                          xivo_swapper.start,
                          args)

    def _mock_parser(self, source_is_git, modules):
        options = mock.Mock()
        options.source_is_git = source_is_git
        options.modules = modules
        parser = mock.Mock()
        parser.parse_args.return_value = options

        return parser


def module_mock(components=[]):
    if components:
        ret = mock.Mock(xivoswap.CompoundModule)
        ret.components = components
    else:
        ret = mock.Mock(xivoswap.PathModule)
    return ret


class TestModuleFactory(unittest.TestCase):
    def setUp(self):
        self._file_swapper = xivoswap.FileSwapper()
        self._factory = xivoswap.ModuleFactory(self._file_swapper)

    def test_create_module(self):
        class ModuleTest(xivoswap.PathModule):
            pass
        xivoswap.register_module('test', ModuleTest)

        result = self._factory.create_module('test')

        self.assertTrue(isinstance(result, ModuleTest))
        self.assertEqual(result._file_swapper, self._file_swapper)


class TestFileSwapper(unittest.TestCase):
    def setUp(self):
        self._file_swapper = xivoswap.FileSwapper()

    @mock.patch('stat.S_ISLNK')
    @mock.patch('subprocess.call')
    @mock.patch('os.lstat')
    def test_link_first_time(self, lstat_mock, call_mock, is_link_mock):
        source_path = '/path/to/package'
        dest_path = '/path/to/git'
        is_link_mock.return_value = False

        self._file_swapper.link_to(source_path, dest_path)

        self.assertTrue(is_link_mock.called)
        call_mock.assert_any_call(['mv', source_path, '%s-orig' % source_path])
        call_mock.assert_any_call(['ln', '-s', dest_path, source_path])

    @mock.patch('stat.S_ISLNK')
    @mock.patch('subprocess.call')
    @mock.patch('os.lstat')
    def test_link_twice_does_nothing(self, lstat_mock, call_mock, is_link_mock):
        source_path = '/path/to/package'
        dest_path = '/path/to/git'
        is_link_mock.return_value = True

        self._file_swapper.link_to(source_path, dest_path)

        self.assertTrue(is_link_mock.called)
        call_mock.assert_not_called()

    @mock.patch('stat.S_ISLNK')
    @mock.patch('subprocess.call')
    @mock.patch('os.lstat')
    def test_restore_first_time(self, lstat_mock, call_mock, is_link_mock):
        package_path = '/path/to/package'
        is_link_mock.return_value = True

        self._file_swapper.restore(package_path)

        self.assertTrue(is_link_mock.called)
        call_mock.assert_any_call(['rm', package_path])
        call_mock.assert_any_call(['mv', '%s-orig' % package_path, package_path])

    @mock.patch('stat.S_ISLNK')
    @mock.patch('subprocess.call')
    @mock.patch('os.lstat')
    def test_restore_twice_does_nothing(self, lstat_mock, call_mock, is_link_mock):
        package_path = '/path/to/package'
        is_link_mock.return_value = False

        self._file_swapper.restore(package_path)

        self.assertTrue(is_link_mock.called)
        call_mock.assert_not_called()
