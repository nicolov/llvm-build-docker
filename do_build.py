#!/usr/bin/env python

"""
This script runs inside docker and downloads, builds, and installs
clang and related tooling.

Inspiration from:
llvm/utils/docker/scripts/build_install_llvm.sh
llvm/utils/release/test-release.sh
"""

from __future__ import print_function

import argparse
import os
import subprocess

FLAGS = None

SVN_BASE_URL = 'http://llvm.org/svn/llvm-project'

#
# Build configuration

SVN_TAG = 'tags/RELEASE_600/final'
ARCHIVE_FILENAME = 'clang-6.0.0-1.tar.xz'

PROJECTS = [
    'llvm',
    'cfe',

    'clang-tools-extra',
    'libcxx',
    'libcxxabi',
    'libunwind',
    'compiler-rt',
]

INSTALL_TARGETS = [
    'install-clang-format',
    'install-clang-headers',
    'install-clang',
    'install-clang-tidy',
    'install-libcxx',
    'install-libcxxabi',
    'install-unwind',
    'install-compiler-rt',
    'install-compiler-rt-headers',
    'install-llvm-symbolizer',
    # Coverage
    'install-llvm-cov',
    'install-llvm-profdata',
    # Sanitizers
    'install-asan',
    'install-lsan',
    'install-msan',
    'install-tsan',
    'install-ubsan',
]


def _destination_dir_for_project(project_name):
    # llvm is particular about the checkout locations of different
    # sub-projects.
    checkout_paths = {
        'llvm': '',
        'cfe': 'tools/clang',
        'clang-tools-extra': 'tools/clang/tools/extra',
    }
    return checkout_paths.get(project_name, 'projects/' + project_name)


def download_sources():
    for p in PROJECTS:
        dest_dir = os.path.join(FLAGS.src_dir, _destination_dir_for_project(p))
        if os.path.exists(dest_dir):
            print('Skipping checkout, as {} exists.'.format(dest_dir))
        else:
            print('Checking out {} to {}'.format(p, dest_dir))
            svn_url = SVN_BASE_URL + '/' + p + '/' + SVN_TAG
            subprocess.check_call([
                'svn', 'export', '-q', svn_url, dest_dir])


def build():
    try:
        os.makedirs(FLAGS.build_dir)
    except OSError:
        pass

    # Configuration
    subprocess.check_call([
        'cmake',
        '-GNinja',
        '-DCMAKE_INSTALL_PREFIX={}'.format(FLAGS.install_dir),
        '-DCLANG_BOOSTRAP_TARGETS="install-clang;install-clang-headers"',
        '-DCLANG_ENABLE_BOOTSTRAP=ON',
        '-DCMAKE_BUILD_TYPE=Release',
        FLAGS.src_dir,
    ], cwd=FLAGS.build_dir)

    # Compile/install
    subprocess.check_call(
        ['ninja'] + INSTALL_TARGETS,
        cwd=FLAGS.build_dir)


def package():
    archive_path = os.path.abspath(ARCHIVE_FILENAME)
    subprocess.check_call(['rm', '-f', archive_path])
    subprocess.check_call(
        ['tar', '-I', 'pxz', '-cf', archive_path, '.'],
        cwd=FLAGS.install_dir)
    subprocess.check_call(['ls', '-lh', archive_path])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--src-dir',
                        default='/tmp/llvm-builder/src', help='Path where the source will be downloaded')
    parser.add_argument('--build-dir',
                        default='/tmp/llvm-builder/build', help='Path to the build scratch dir')
    parser.add_argument('--install-dir',
                        default='/tmp/llvm-builder/install')
    FLAGS = parser.parse_args()

    download_sources()
    build()
    package()

    print('To clean up, run:\n\t', ' && '.join(
        ['rm -rf ' + p for p in [FLAGS.src_dir, FLAGS.build_dir, FLAGS.install_dir]]))
