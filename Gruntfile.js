// Generated on 2014-06-25 using generator-poro 0.0.2
module.exports = function (grunt) {
	'use strict';
	var path = require('path'),
		sass = require('node-sass'),
		process = require('process'),
		buildoutBin = path.join(path.dirname(__filename), 'bin'),
		rootPath = process.cwd(),
		publicRootPath = path.join('appengine', 'src', 'greenday_public'),
		paths = {
			staticDevRoot: path.join(publicRootPath, 'static-dev'),
			staticDistRoot: path.join(publicRootPath, 'static'),
			tmp: path.join(rootPath, '.tmp'),
			templates: path.join(publicRootPath, 'templates')
		},
		config = {
			pkg: grunt.file.readJSON('package.json'),
			rootPath: rootPath,
			publicRootPath: publicRootPath,
			paths: paths,
			sass: {
				options: {
					implementation: sass,
					sourceMap: true
				}
			}
		};

	// Ensure buildout-installed executables are used over globally-installed versions
	process.env.PATH = buildoutBin + ':' + process.env.PATH;

	grunt.initConfig(config);

	require('load-grunt-config')(grunt, {
		configPath: path.join(process.cwd(), 'grunt', 'tasks'),
		config: config
	});

	grunt.task.run('notify_hooks');

};
