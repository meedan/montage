/**
 * pages.welcome Module
 *
 * The welcome page module.
 */
(function () {
  angular
    .module('pages')
    .controller('WelcomePageCtrl', WelcomePageCtrl);

  /** @ngInject */
  function WelcomePageCtrl($scope, $location, PageService, UserService) {
    var ctrl = this;

    PageService.updatePageData({
      title: 'Montage',
      loading: false
    });

    $scope.$on('user:signIn:complete', function( ) {
      $location.path('/');
    });

    ctrl.logIn = logIn;
    ctrl.isBusy = false;
		ctrl.imOnWelcomePage = true;

    function logIn() {
      UserService
        .getUser(false)
        .then(function() {
          var nextUrl = $location.search().next || '/';
          $location.url(nextUrl);
        });
    }
  }
}());
