/**
 * Main application config
 */
(function() {
  angular
    .module('app')
    .config(appConfig)
		.config(themeConfig);

  /** @ngInject */
  function appConfig($compileProvider, $httpProvider, $locationProvider,
    $logProvider, $mdThemingProvider, uiGmapGoogleMapApiProvider, oAuthParams,
    localStorageServiceProvider, hotkeysProvider) {

    if (!window.DEBUG) {
      $compileProvider.debugInfoEnabled(false);
      $logProvider.debugEnabled(false);
    }

    $locationProvider.html5Mode(true);

    ///////////////////////////////////
    // $http
    ///////////////////////////////////
    $httpProvider.defaults.headers.common['X-CSRFToken'] = $('input[name=csrfmiddlewaretoken]').val();
    $httpProvider.defaults.headers.common['Content-Type'] = 'application/json';

    ///////////////////////////////////
    // Angular UI Google Maps
    ///////////////////////////////////
    uiGmapGoogleMapApiProvider.configure({
      key: oAuthParams.api_key,
      v: '3.17',
      libraries: 'geometry,places'
    });

    ///////////////////////////////////
    // angular-local-storage
    ///////////////////////////////////
    localStorageServiceProvider.setPrefix('greenDay');

    ///////////////////////////////////
    // angular-hotkeys
    ///////////////////////////////////
    hotkeysProvider.template = '<div ng-include="\'components/gd-hotkeys/gd-hotkeys.html\'"></div>';
  }

	/** @ngInject */
  function themeConfig($mdThemingProvider) {
    $mdThemingProvider.definePalette('accent', {
      '50': '#ffffff',
      '100': '#ffd9bd',
      '200': '#ffb985',
      '300': '#ff903d',
      '400': '#ff7f1f',
      '500': '#ff6d00',
      '600': '#e06000',
      '700': '#c25300',
      '800': '#a34600',
      '900': '#853900',
      'A100': '#ffffff',
      'A200': '#ffd9bd',
      'A400': '#ff7f1f',
      'A700': '#c25300',
      'contrastDefaultColor': 'light',
      'contrastDarkColors': '50 100 200 300 400 500 A100 A200 A400'
    });

    $mdThemingProvider.definePalette('topfrontbar', {
      '50': '#a6a6a6',
      '100': '#7f7f7f',
      '200': '#636363',
      '300': '#404040',
      '400': '#303030',
      '500': '#212121',
      '600': '#121212',
      '700': '#020202',
      '800': '#000000',
      '900': '#000000',
      'A100': '#a6a6a6',
      'A200': '#7f7f7f',
      'A400': '#303030',
      'A700': '#020202',
      'contrastDefaultColor': 'light',
      'contrastDarkColors': '50 A100'
    });

    $mdThemingProvider.definePalette('mainBG', {
      '50': '#ffffff',
      '100': '#ffffff',
      '200': '#ffffff',
      '300': '#ffffff',
      '400': '#fdfdfd',
      '500': '#eeeeee',
      '600': '#dfdfdf',
      '700': '#cfcfcf',
      '800': '#c0c0c0',
      '900': '#b1b1b1',
      'A100': '#ffffff',
      'A200': '#ffffff',
      'A400': '#fdfdfd',
      'A700': '#cfcfcf',
      'contrastDefaultColor': 'light',
      'contrastDarkColors': '50 100 200 300 400 500 600 700 800 900 A100 A200 A400 A700'
    });

		$mdThemingProvider.theme('default')
	    .primaryPalette('topfrontbar')
	    .accentPalette('accent',{
        'default': '500',
      })
  	 .warnPalette('accent')
	   .backgroundPalette('mainBG');
  }


}());
