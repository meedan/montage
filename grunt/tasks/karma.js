module.exports = function (grunt) {
  var utils = require('../config/utils.js')(grunt),
      paths = grunt.config('paths'),
      jsFiles = utils.getJsFiles(),
      preprocessors = {};

  jsFiles.forEach(function (value, key) {
    preprocessors[value] = ['coverage'];
  });

  return {
    options: {
      autoWatch: true,
      frameworks: ['jasmine'],
      browsers: ['PhantomJS'],
      reporters: ['coverage', 'mocha'],
      plugins: [
        'karma-mocha-reporter',
        'karma-chrome-launcher',
        'karma-phantomjs-launcher',
        'karma-jasmine',
        'karma-coverage'
      ],
      preprocessors: preprocessors,
      coverageReporter: {
        type : 'html',
        // where to store the report
        dir : 'target/'
      },
      files: utils.getTestFiles()
    },
    unit: {
      autoWatch: true,
      background: true
    },
    unitSingle: {
      singleRun: true
    }
  };
};
