(function () {
	angular
		.module('app.resources')
		.factory('CollaboratorModel', CollaboratorModel)
		.factory('CollaboratorService', CollaboratorService);

	/** @ngInject */
	function CollaboratorModel(DS) {
		return DS.defineResource({
			name: 'collaborator',
			endpoint: 'users',
			relations: {
				belongsTo: {
					project: {
						parent: true,
						localField: 'project',
						localKey: 'project_id'
					}
				}
			}
		});
	}

	/** @ngInject */
	function CollaboratorService(CollaboratorModel) {
		var service = {
			bindAll: bindAll,
			create: create,
			createInstance: createInstance,
			get: get,
			update: update,
			remove: remove,
			list: list
		};

		return service;

		function bindAll(params, scope, expr) {
			return CollaboratorModel.bindAll(params, scope, expr);
		}

		function list(projectId) {
			return CollaboratorModel.findAll({project_id: projectId});
		}

		function get(collaboratorId) {
			return CollaboratorModel.find(collaboratorId);
		}

		function create(collaborator) {
			return CollaboratorModel.create(collaborator);
		}

		function createInstance(collaborator) {
			return CollaboratorModel.createInstance(collaborator);
		}

		function update(collaborator) {
			return CollaboratorModel.save(collaborator);
		}

		function remove(collaboratorId) {
			return CollaboratorModel.destroy(collaboratorId);
		}
	}
}());
