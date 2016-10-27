(function () {

  angular
		.module('app.services')
		.factory('HeapService', HeapService);

    /** @ngInject */
    function HeapService($rootScope) {
      return {
        engage: engage
      };

      function engage(){
        $rootScope.$on('user:signIn:complete', function(user) {
          console.log(user);
        });
      }

    }
})();
