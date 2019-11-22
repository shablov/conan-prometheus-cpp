#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import shutil
from conans import ConanFile, CMake, tools
from conans.errors import ConanInvalidConfiguration
from conans.model.version import Version


class PrometheusCppConan(ConanFile):
    name = 'prometheus-cpp'
    version = '0.7.0'
    license = 'MIT'
    url = 'https://github.com/shablov/conan-prometheus-cpp'
    homepage = 'https://github.com/jupp0r/prometheus-cpp'
    description = 'This library aims to enable Metrics-Driven Development for C++ services'
    topics = (
        'conan',
        'prometheus-cpp',
        'metrics',
        'measure',
        'statistics',
        'profile',
        'log',
    )
    author = 'Dmitriy Shablov <dzmitriy.shablov@gmail.com>'
    settings = ('os', 'compiler', 'build_type', 'arch')
    options = {
        'shared': [True, False],
        'fPIC': [True, False],
        'mode': ['pull', 'push'],
        'enable_compression': [True, False],
        'override_cxx_standard_flags': [True, False],
    }
    default_options = {
        'shared': False,
        'fPIC': True,
        'mode': 'pull',
        'enable_compression': True,
        'override_cxx_standard_flags': True,
    }
    _source_subfolder = 'source_subfolder'
    _build_subfolder = 'build_subfolder'
    exports = 'LICENSE.md'
    exports_sources = ['CMakeLists.txt', _source_subfolder]
    generators = 'cmake'

    def config_options(self):
        if self.settings.os == 'Windows':
            self.options.remove('fPIC')

    def source(self):
        tools.get('%s/archive/v%s.zip' % (self.homepage, self.version))
        os.rename('prometheus-cpp-%s' % self.version,
                  self._source_subfolder)
        os.rename(os.path.join(self._source_subfolder, 'CMakeLists.txt'
                               ), os.path.join(self._source_subfolder,
                                               'CMakeListsOriginal.txt'))
        shutil.move('CMakeLists.txt',
                    os.path.join(self._source_subfolder,
                                 'CMakeLists.txt'))

    def configure(self):
        if self.settings.compiler == "Visual Studio" and \
           Version(self.settings.compiler.version.value) < "14":
            raise ConanInvalidConfiguration(
                "Prometheus-cpp does not support MSVC < 14")

    def requirements(self):
        if self.options.mode == 'pull':
            self.requires('civetweb/1.11@conan-shablov/stable')
            if self.options.enable_compression:
                self.requires.add('zlib/1.2.11@conan/stable')
        else:  # self.options.mode == 'push':
            self.requires.add('libcurl/7.64.1@bincrafters/stable')

    def _configure_cmake(self):
        cmake = CMake(self)
        cmake.definitions['BUILD_SHARED_LIBS'] = self.options.shared

        if self.settings.os != 'Windows':
            cmake.definitions['CMAKE_POSITION_INDEPENDENT_CODE'] = \
                self.options.fPIC

        cmake.definitions['ENABLE_PULL'] = self.options.mode == 'pull'
        cmake.definitions['ENABLE_PUSH'] = self.options.mode == 'push'
        cmake.definitions['ENABLE_COMPRESSION'] = \
            self.options.enable_compression
        cmake.definitions['OVERRIDE_CXX_STANDARD_FLAGS'] = \
            self.options.override_cxx_standard_flags

        cmake.definitions['ENABLE_TESTING'] = False
        cmake.definitions['USE_THIRDPARTY_LIBRARIES'] = False

        cmake.configure(build_folder=self._build_subfolder,
                        source_folder=self._source_subfolder)
        return cmake

    def build(self):
        cmake = self._configure_cmake()
        cmake.build()

    def package(self):
        cmake = self._configure_cmake()
        cmake.install()
        self.copy('LICENSE', dst='licenses', src=self._source_subfolder)
        self.copy('LICENSE.md', dst='licenses')

    def imports(self):
        self.copy("*.dll", dst="bin", src="bin")
        self.copy("*.dylib", dst="bin", src="lib")
        self.copy("*.so", dst="bin", src="lib")

    def package_info(self):    
        if self.options.mode == 'pull':
            self.cpp_info.libs.append('prometheus-cpp-pull')
        else:  # self.options.mode == 'push':
            self.cpp_info.libs.append('prometheus-cpp-push')
        self.cpp_info.libs.append("prometheus-cpp-core")

        if self.settings.os == 'Linux':
            self.cpp_info.libs.extend(["dl", "rt", "pthread"])

        # gcc's atomic library not linked automatically on clang
        if self.settings.compiler == 'clang':
            self.cpp_info.libs.append('atomic')
