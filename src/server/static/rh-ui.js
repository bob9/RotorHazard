
var rhui = {
	_modelField: function (field_options) {
		var settings = {
			data: {},
			desc: null,
			html_attributes: {},
			fieldClass: null,
			field_type: null,
			genericOption: null,
			id: null,
			label: null,
			options: null,
			placeholder: null,
			value: null,
			wrapperEl: null,
			wrapperClass: null
		}

		for (item in settings) {
			if (field_options[item] != null) {
				settings[item] = field_options[item];
			}
		}

		return settings;
	},
	buildField: function(field_options) {
		var settings = this._modelField(field_options);

		if (settings.wrapperEl) {
			var wrapper = $('<' + settings.wrapperEl + '>');
		} else {
			var wrapper = $('<div>');
		}

		if (!settings.id) {
			settings.id = 'setting_' + window.performance.now()
		}

		if (settings.wrapperClass) {
			wrapper.addClass(settings.wrapperClass);
		}

		var labelWrap = $('<div class="label-block"></div>');

		var label = $('<label>')
			.attr('for', settings.id)
			.text(__(settings.label));

		labelWrap.append(label);

		if (settings.desc) {
			labelWrap.append('<p class="desc">' + settings.desc + '</p>');
		}

		if (settings.field_type == 'text') {
			var field = $('<input>')
				.attr('type', 'text')
				.attr('placeholder', settings.placeholder);
			if ('minlength' in settings.html_attributes) {
				field.attr('minlength', settings.html_attributes.minlength)
			}
			if ('maxlength' in settings.html_attributes) {
				field.attr('maxlength', settings.html_attributes.maxlength)
			}
			if ('pattern' in settings.html_attributes) {
				field.attr('pattern', settings.html_attributes.pattern)
			}
			wrapper.append(labelWrap);
			wrapper.append(field);
		} else if (settings.field_type == 'password') {
			var field = $('<input>')
				.attr('type', 'text')
				.addClass('uifield-password')
				.attr('placeholder', settings.placeholder);
			if ('minlength' in settings.html_attributes) {
				field.attr('minlength', settings.html_attributes.minlength)
			}
			if ('maxlength' in settings.html_attributes) {
				field.attr('maxlength', settings.html_attributes.maxlength)
			}
			if ('pattern' in settings.html_attributes) {
				field.attr('pattern', settings.html_attributes.pattern)
			}
			wrapper.append(labelWrap);
			wrapper.append(field);
		} else if (settings.field_type == 'basic_int') {
			var field = $('<input>')
				.attr('type', 'number')
				.attr('min', 0)
				.attr('max', 999)
				.attr('step', 1)
				.attr('placeholder', settings.placeholder);
			wrapper.append(labelWrap);
			wrapper.append(field);
		} else if (settings.field_type == 'number') {
			var field = $('<input>')
				.attr('type', 'number')
				.attr('placeholder', settings.placeholder);

			if ('min' in settings.html_attributes) {
				field.attr('min', settings.html_attributes.min)
			}
			if ('max' in settings.html_attributes) {
				field.attr('max', settings.html_attributes.max)
			}
			if ('step' in settings.html_attributes) {
				field.attr('step', settings.html_attributes.step)
			}
			wrapper.append(labelWrap);
			wrapper.append(field);
		} else if (settings.field_type == 'range') {
			var field = $('<input>')
				.attr('type', 'range')
				.attr('placeholder', settings.placeholder);

			if ('min' in settings.html_attributes) {
				field.attr('min', settings.html_attributes.min)
			}
			if ('max' in settings.html_attributes) {
				field.attr('max', settings.html_attributes.max)
			}
			if ('step' in settings.html_attributes) {
				field.attr('step', settings.html_attributes.step)
			}
			wrapper.append(labelWrap);
			wrapper.append(field);
		} else if (settings.field_type == 'select') {
			var field = $('<select>')

			for (var opt_id in settings.options) {
				var opt = settings.options[opt_id];

				var opt_el = $('<option>')
					.attr('value', opt.value)
					.text(opt.label);
				field.append(opt_el);
			}
			if (!settings.value) {
				settings.value = settings.options[0].name;
			}
			wrapper.append(labelWrap);
			wrapper.append(field);
		} else if (settings.field_type == 'checkbox') {
			var field = $('<input>')
				.attr('type', 'checkbox')
			wrapper.append(labelWrap);
			wrapper.append(field);
		} else if (settings.field_type == 'date') {
			var field = $('<input>')
				.attr('type', 'date')

			if ('min' in settings.html_attributes) {
				field.attr('min', settings.html_attributes.min)
			}
			if ('max' in settings.html_attributes) {
				field.attr('max', settings.html_attributes.max)
			}
			if ('step' in settings.html_attributes) {
				field.attr('step', settings.html_attributes.step)
			}
			wrapper.append(labelWrap);
			wrapper.append(field);
		} else if (settings.field_type == 'time') {
			var field = $('<input>')
				.attr('type', 'time')

			if ('min' in settings.html_attributes) {
				field.attr('min', settings.html_attributes.min)
			}
			if ('max' in settings.html_attributes) {
				field.attr('max', settings.html_attributes.max)
			}
			if ('step' in settings.html_attributes) {
				field.attr('step', settings.html_attributes.step)
			}
			wrapper.append(labelWrap);
			wrapper.append(field);
		} else if (settings.field_type == 'datetime') {
			var field = $('<input>')
				.attr('type', 'datetime-local')

			if ('min' in settings.html_attributes) {
				field.attr('min', settings.html_attributes.min)
			}
			if ('max' in settings.html_attributes) {
				field.attr('max', settings.html_attributes.max)
			}
			if ('step' in settings.html_attributes) {
				field.attr('step', settings.html_attributes.step)
			}
			wrapper.append(labelWrap);
			wrapper.append(field);
		} else if (settings.field_type == 'email') {
			var field = $('<input>')
				.attr('type', 'email')
				.attr('placeholder', settings.placeholder);

			if ('minlength' in settings.html_attributes) {
				field.attr('minlength', settings.html_attributes.minlength)
			}
			if ('maxlength' in settings.html_attributes) {
				field.attr('maxlength', settings.html_attributes.maxlength)
			}
			if ('pattern' in settings.html_attributes) {
				field.attr('pattern', settings.html_attributes.pattern)
			}
			if ('multiple' in settings.html_attributes) {
				field.prop('multiple', true);
			}
			wrapper.append(labelWrap);
			wrapper.append(field);
		} else if (settings.field_type == 'tel') {
			var field = $('<input>')
				.attr('type', 'tel')
			if ('minlength' in settings.html_attributes) {
				field.attr('minlength', settings.html_attributes.minlength)
			}
			if ('maxlength' in settings.html_attributes) {
				field.attr('maxlength', settings.html_attributes.maxlength)
			}
			if ('pattern' in settings.html_attributes) {
				field.attr('pattern', settings.html_attributes.pattern)
			}
			wrapper.append(labelWrap);
			wrapper.append(field);
		} else if (settings.field_type == 'url') {
			var field = $('<input>')
				.attr('type', 'url')
			if ('minlength' in settings.html_attributes) {
				field.attr('minlength', settings.html_attributes.minlength)
			}
			if ('maxlength' in settings.html_attributes) {
				field.attr('maxlength', settings.html_attributes.maxlength)
			}
			if ('pattern' in settings.html_attributes) {
				field.attr('pattern', settings.html_attributes.pattern)
			}
			wrapper.append(labelWrap);
			wrapper.append(field);
		} else {
			console.log('fieldtype not supported');
			return false;
		}

		field.addClass(settings.fieldClass)
			.attr('id', settings.id)

		if (settings.genericOption) {
			field.addClass('set-option')
				.data('option', settings.genericOption)
		}

		for (var idx in settings.data) {
			field.data(idx, settings.data[idx])
		}

		this.updateField(field_options, field);
		return wrapper
	},
	updateField: function(field_options, element) {
		var settings = this._modelField(field_options);

		if (settings.field_type == 'checkbox') {
			element.prop('checked', settings.value);
		} else {
			element.val(settings.value);
		}

		for (var idx in settings.data) {
			element.data(idx, settings.data[idx])
		}
	},
	getFieldVal: function(element) {
		var el = $(element);
		var field = el.data('field');

		if (el.attr('type') == 'checkbox') {
			value = el.prop('checked');
		} else {
			value = el.val();
		}

		return value;
	},
	buildQuickbuttons: function(btn_list) {
		var btn_list_el = $('<div class="control-set">');
		for (var idx in btn_list) {
			btn_el = $('<button>')
				.addClass('quickbutton')
				.text(btn_list[idx].label)
				.data('btn_id', btn_list[idx].name)

			btn_list_el.append(btn_el)
		}
		return btn_list_el
	}
}

$(document).ready(function () {
	$(document).on('click', '.quickbutton', function (event) {
		var data = {
			id: $(this).data('btn_id'),
			namespace: 'quickbutton'
		};
		socket.emit('dispatch_event', data);
	});
});
