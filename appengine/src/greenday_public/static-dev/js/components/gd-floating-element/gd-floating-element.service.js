(function() {
	angular.module('components.floatingElement')
		.factory('floatingElementService', floatingElementService);

	/** @ngInject */
	function floatingElementService(_, $q, $compile, $rootScope, $timeout, backdropService) {
		var feStack = {},
			service = {
				show: show,
				hide: hide,
				reposition: reposition,
				positionElement: positionElement
			};

		return service;

		/////////////////////

		function show(directiveType, options) {
			var fe = new FloatingElement(directiveType, options);
			feStack[fe.id] = fe;
			return fe;
		}

		function hide(id, data) {
			var fe = feStack[id];

			if (!angular.isDefined(id)) {
				throw new TypeError('No id passed to floatingElementService.hide()');
			}

			if (!fe) {
				return;
			}

			// Remove the floating element from the dom.
			fe.element.remove();

			// We are safe to destroy the floating element scope because we
			// explicitly created a child scope specifically for the floating
			// element component so as not so clobber the passed in scope.
			fe.scope.$destroy();

			// We may not have a backdrop as not all usages of floating element
			// require one (e.g. floating elements which are shown only
			// on hover).
			if (fe.backdrop) {
				backdropService.remove(fe.backdrop.id);
			}

			fe._dfd.resolve(data);

			delete feStack[id];
		}

		function reposition(id) {
			var fe = feStack[id];

			if (!angular.isDefined(id)) {
				throw new TypeError('No id passed to floatingElementService.reposition()');
			}

			if (!fe) {
				throw new ReferenceError('No floating element with id "'+ id + '"');
			}

			positionElement(fe.element, fe.options.trigger, fe.options.positioning);
		}

		// FIXME: Is there a nicer way to do this, something like the "locals"
		// injection in angular material?
		function getAttributes(attributes) {
			var attributesString = '';

			if (!angular.isObject(attributes)) {
				attributes = {};
			}

			angular.forEach(attributes, function (value, key) {
				attributesString += key + '="' + value  + '" ';
			});

			if (attributesString !== '') {
				attributesString = ' ' + attributesString.trim();
			}

			return attributesString;
		}

		function positionElement($element, $triggerElement, positioningOptions) {
			var alignTo,
				alignEdge,
				alignOffset = { x: 0, y: 0 },
				floatingElementDimensions,
				floatingElementOffset = { x: 0, y: 0 },
				triggerElementDimensions,
				triggerElementOffset = $triggerElement.offset();

			alignTo	= {
				x: null,
				y: null
			};

			alignEdge = {
				x: null,
				y: null
			};

			// Get the floating elements dimensions.
			floatingElementDimensions = {
				height: $element.outerHeight(),
				width: $element.outerWidth()
			};

			triggerElementDimensions = {
				height: $triggerElement.outerHeight(),
				width: $triggerElement.outerWidth()
			};

			// Calculate the floating element offset, respecting the specified
			// align-to setting.
			if (positioningOptions.position === 'outside') {
				// position: outside
				alignTo.y = positioningOptions.alignTo.split(' ')[0];
				alignTo.x = positioningOptions.alignTo.split(' ')[1];

				alignEdge.y = positioningOptions.alignEdge.split(' ')[0];
				alignEdge.x = positioningOptions.alignEdge.split(' ')[1];
			} else {
				// position: inside
				alignTo.y = positioningOptions.alignTo.split(' ')[0];
				alignTo.x = positioningOptions.alignTo.split(' ')[1];

				alignEdge.y = alignTo.y;
				alignEdge.x = alignTo.x;
			}

			// Get the coordinates of the trigger element offset point,
			// computed by taking the trigger elements offset and adjusting
			// for the required corner.
			switch (alignTo.x) {
				case 'right':
					alignOffset.x =
						triggerElementOffset.left + triggerElementDimensions.width;
				break;

				case 'center':
					alignOffset.x =
						triggerElementOffset.left +
							(triggerElementDimensions.width / 2);
				break;

				default:
					// No need to do anything as the offset it top left
					// by default.
					alignOffset.x = triggerElementOffset.left;
				break;
			}

			switch (alignTo.y) {
				case 'bottom':
					alignOffset.y =
						triggerElementOffset.top + triggerElementDimensions.height;
				break;

				case 'center':
					alignOffset.y =
						triggerElementOffset.top +
							(triggerElementDimensions.height / 2);
				break;

				default:
					// No need to do anything as the offset it top left
					// by default.
					alignOffset.y = triggerElementOffset.top;
				break;
			}

			// At this point alignOffset is the location of the point at
			// which the floating element needs to position itself based on.
			// We now need to position the floating element based on this
			// coordinate, taking into account the desired edge of the
			// floating element which should align with this position.
			switch (alignEdge.x) {
				case 'left':
					floatingElementOffset.x =
						alignOffset.x +
						positioningOptions.gaps.x;
				break;

				case 'center':
					floatingElementOffset.x =
						alignOffset.x -
						(floatingElementDimensions.width / 2);
				break;

				case 'right':
					floatingElementOffset.x =
						alignOffset.x -
						(positioningOptions.gaps.x +
						floatingElementDimensions.width);
				break;
			}

			switch (alignEdge.y) {
				case 'top':
					floatingElementOffset.y =
						alignOffset.y +
						positioningOptions.gaps.y;
				break;

				case 'center':
					floatingElementOffset.y =
						alignOffset.y -
						(floatingElementDimensions.height / 2);
				break;

				case 'bottom':
					floatingElementOffset.y =
						alignOffset.y -
						(positioningOptions.gaps.y +
						floatingElementDimensions.height);
				break;
			}

			// Set the floating elements position.
			$element.css({
				left: floatingElementOffset.x + 'px',
				top: floatingElementOffset.y + 'px'
			});
		}

		function FloatingElement(directiveType, options) {
			var self = this,
				defaults,
				html,
				id = _.uniqueId('fe-' + directiveType + '-'),
				linkFn;

			defaults = {
				backdrop: true,
				positioning: angular.extend({
					'position': 'outside',
					'align': 'above center'
				}, options.positioning),
				zIndex: 2000
			};

			options = angular.extend({}, defaults, options);

			if (angular.isDefined(options.positioning.gaps)) {
				options.positioning.gaps = angular.extend({},
					{ x: 0, y: 0 },
					options.positioning.gaps
				);
			}

			// Generate markup
			html = [
				'<gd-floating-element id="' + id + '">',
					'<' + directiveType + getAttributes(options.attributes),
					'></' + directiveType + '>',
				'</gd-floating-element>'
			].join('');

			// Compile
			linkFn = $compile(html);

			this.id = id;
			this.scope = options.scope.$new(false);
			this.element = linkFn(this.scope);
			this.options = options;
			this._dfd = $q.defer();
			this.promise = this._dfd.promise;

			// Ensure the element is temporarily hidden while we measeure and
			// position it.
			this.element.addClass('gd-hide-override');

			// Attach to the page
			$('body').append(this.element);

			// Set the popups z-index so it stacks as required.
			this.element.css('zIndex', this.options.zIndex);

			// I hate myself right now. For some reason the child DOM doesn't
			// appear to exist until after the next tick, but AFAIK $compile
			// isn't async :|
			$timeout(function () {
				positionElement(self.element, options.trigger, options.positioning);
				self.element.removeClass('gd-hide-override');
			});

			if (options.backdrop) {
				// Add the backdrop
				this.backdrop = backdropService.add({
					zIndex: this.options.zIndex - 1
				});

				this.backdrop.promise.then(function() {
					hide(self.id);
				});
			}
		}
	}
}());
