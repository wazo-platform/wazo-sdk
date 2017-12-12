import tempfile
import unittest
import shutil
import xivoswap
import subprocess
import os
import stat


class TestXiVOSwapIntegration(unittest.TestCase):
    def setUp(self):
        self._root = tempfile.mkdtemp()
        self._create_modules()
        self._assembler = xivoswap.Assembler()

    def _create_modules(self):
        class ModuleTest1(xivoswap.PathModule):
            package = '%s/package/test1' % self._root
            git = '%s/git/test1' % self._root

        xivoswap.register_module('test1', ModuleTest1)

        class ModuleCompound1(xivoswap.CompoundModule):
            components = ['test1', 'test2']

        xivoswap.register_module('compound1', ModuleCompound1)

        class ModuleTest2(xivoswap.PathModule):
            package = '%s/package/test2' % self._root
            git = '%s/git/test2' % self._root

        xivoswap.register_module('test2', ModuleTest2)

    def tearDown(self):
        shutil.rmtree(self._root)

    def test_replace_single_by_git(self):
        self._create_unlinked_tree()

        self._assembler.start(['-g', 'test1'])

        self.assertTrue(self._is_link('%s/package/test1' % self._root))
        self.assertFalse(self._is_link('%s/package/test2' % self._root))

    def test_replace_compound_by_git(self):
        self._create_unlinked_tree()

        self._assembler.start(['-g', 'compound1'])

        self.assertTrue(self._is_link('%s/package/test1' % self._root))
        self.assertTrue(self._is_link('%s/package/test2' % self._root))

    def test_restore_single_to_package(self):
        self._create_linked_tree()

        self._assembler.start(['-p', 'test1'])

        self.assertFalse(self._is_link('%s/package/test1' % self._root))
        self.assertTrue(self._is_link('%s/package/test2' % self._root))

    def test_restore_compound_to_package(self):
        self._create_linked_tree()

        self._assembler.start(['-p', 'compound1'])

        self.assertFalse(self._is_link('%s/package/test1' % self._root))
        self.assertFalse(self._is_link('%s/package/test2' % self._root))

    def _is_link(self, path):
        path_stat = os.lstat(path)
        return stat.S_ISLNK(path_stat.st_mode)

    def _create_unlinked_tree(self):
        self._create_unlinked_subtree('package')
        self._create_unlinked_subtree('git')

    def _create_linked_tree(self):
        self._create_unlinked_subtree('git')
        self._create_linked_subtree('package', 'git')

    def _create_unlinked_subtree(self, version):
        for num in range(1, 3):
            path = '%s/%s/test%s' % (self._root, version, num)
            subprocess.call(['mkdir', '-p', path])

    def _create_linked_subtree(self, from_version, to_version):
        source_path_root = '%s/%s' % (self._root, from_version)
        subprocess.call(['mkdir', '-p', source_path_root])
        for num in range(1, 3):
            target_path = '%s/%s/test%s' % (self._root, to_version, num)
            source_path = '%s/%s/test%s' % (self._root, from_version, num)
            subprocess.call(['ln', '-s', target_path, source_path])
            subprocess.call(['mkdir', '-p', '%s-orig' % source_path])
