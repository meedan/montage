(function() {
	angular.module('components.popup')
		.factory('popupFactory', function (_, $log, $q, $timeout, POPUP_DEFAULTS, backdropService) {
			var factory = {
				getInstance: function (options) {
					return new Popup(options);
				}
			};

			function Popup(options) {
				var self = this,
					html,
					id = _.uniqueId('popup:'),
					opts = angular.extend({}, POPUP_DEFAULTS, options);

				this.id = id;
				this.options = opts;
				this._dfd = $q.defer();
				this.promise = this._dfd.promise;

				this.setOptions(opts);

				return this;
			}

			Popup.prototype.setElement = function (element) {
				this.$element = element;
			};

			Popup.prototype.setOptions = function (options) {
				// Convert options to correct type.
				this.options.gapX = parseInt(options.gapX, 10);
				this.options.gapY = parseInt(options.gapY, 10);

				if (options.backdrop === 'true') {
					this.options.backdrop = true;
				} else {
					this.options.backdrop = false;
				}
			};

			Popup.prototype.position = function() {
				var alignTo,
					alignEdge,
					alignOffset = { x: 0, y: 0 },
					floatingElementDimensions,
					floatingElementOffset = { x: 0, y: 0 },
					positioningOptions = this.options,
					triggerElementDimensions,
					triggerElementOffset = this.$triggerElement.offset();

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
					height: this.$element.outerHeight(),
					width: this.$element.outerWidth()
				};

				triggerElementDimensions = {
					height: this.$triggerElement.outerHeight(),
					width: this.$triggerElement.outerWidth()
				};

				// Calculate the floating element offset, respecting the specified
				// align-to setting.

				// position: outside
				if (positioningOptions.position === 'outside') {
					alignTo.y = positioningOptions.alignTo.split(' ')[0];
					alignTo.x = positioningOptions.alignTo.split(' ')[1];

					alignEdge.y = positioningOptions.alignEdge.split(' ')[0];
					alignEdge.x = positioningOptions.alignEdge.split(' ')[1];

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
								positioningOptions.gapX;
						break;

						case 'center':
							floatingElementOffset.x =
								alignOffset.x -
								(floatingElementDimensions.width / 2);
						break;

						case 'right':
							floatingElementOffset.x =
								alignOffset.x -
								(positioningOptions.gapX +
								floatingElementDimensions.width);
						break;
					}

					switch (alignEdge.y) {
						case 'top':
							floatingElementOffset.y =
								alignOffset.y +
								positioningOptions.gapY;
						break;

						case 'center':
							floatingElementOffset.y =
								alignOffset.y -
								(floatingElementDimensions.height / 2);
						break;

						case 'bottom':
							floatingElementOffset.y =
								alignOffset.y -
								(positioningOptions.gapY +
								floatingElementDimensions.height);
						break;
					}
				}

				// Set the floating elements position.
				this.$element.css({
					left: floatingElementOffset.x + 'px',
					top: floatingElementOffset.y + 'px'
				});
			};

			Popup.prototype.open = function($triggerElement) {
				this.$triggerElement = $triggerElement;

				// Ensure the element is temporarily hidden while we measure and
				// position it.
				this.$element.addClass('gd-hide-override');

				// Set the popups z-index so it stacks as required.
				this.$element.css('zIndex', this.options.zIndex);

				this.options.attachTo.append(this.$element);

				// This is nasty... for some reason the child DOM doesn't
				// appear to exist until after the next tick, not sure why :/.
				$timeout(function () {
					this.position();
					this.$element.removeClass('gd-hide-override');
				}.bind(this));

				if (this.options.backdrop) {
					// Ensure the backdrop for this popup always appears below
					// this popup layer by adjusting the z-index.
					this.backdrop = backdropService.add({
						zIndex: this.options.zIndex - 1
					});

					this.backdrop.promise.then(function() {
						this.close();
					}.bind(this));
				}

				return this.promise;
			};

			Popup.prototype.close = function() {
				backdropService.remove(this.backdrop.id, false);

				this.$element.remove();
				this.$triggerElement = null;

				this._dfd.resolve();
			};

			return factory;
		});
}());
