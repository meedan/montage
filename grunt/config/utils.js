module.exports = function (grunt) {
	'use strict';
	var path = require('path'),
		rootPath = grunt.config('rootPath'),
		paths = grunt.config('paths'),
		jsFileList = grunt.file.expand([
			paths.staticDevRoot + '/js/**/*.js',
			'!' + paths.staticDevRoot + '/js/**/*.spec.js'
		]),
		testFileList = grunt.file.expand([
			paths.staticDevRoot + '/libs/angular-mocks/angular-mocks.js',
			paths.staticDevRoot + '/js/**/*.spec.js'
		]),
		useminListFile = path.join(paths.staticDevRoot, 'filelist.json');

	return {
		getTestFiles: function () {
			var libFiles = [],
				appJsFiles = [],
				karmaTestFiles = [];

			try {
				var fileList = grunt.file.readJSON(useminListFile);
				libFiles = fileList.libs;
				appJsFiles = fileList.app;
			} catch(e) {
				appJsFiles = jsFileList;
			}

			karmaTestFiles = [].concat(libFiles, appJsFiles, testFileList);

			return karmaTestFiles;
		},
		getJsFiles: function () {
			return jsFileList;
		}
	};
};
