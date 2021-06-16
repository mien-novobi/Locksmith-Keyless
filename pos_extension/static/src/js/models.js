odoo.define('pos_extension.models', function (require) {
    "use strict";

    var models = require('point_of_sale.models');


    var _super_order = models.Order.prototype;

    models.Order = models.Order.extend({
        initialize: function () {
            _super_order.initialize.apply(this, arguments);

            this.to_invoice = this.pos.config.module_account && this.pos.config.auto_invoice;
            this.to_sms = this.pos.config.sms_notify && this.pos.config.auto_sms_notify;
        },
        export_as_JSON: function () {
            var json = _super_order.export_as_JSON.apply(this, arguments);
            json.to_sms = this.to_sms;
            return json;
        },
        set_to_sms: function (to_sms) {
            this.to_sms = to_sms;
        },
        is_to_sms: function () {
            return this.to_sms;
        },
    });

});
