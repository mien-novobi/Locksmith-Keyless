odoo.define('pos_extension.screens', function (require) {
    "use strict";

    var screens = require('point_of_sale.screens');


    var PaymentScreenWidget = screens.PaymentScreenWidget;

    PaymentScreenWidget.include({
        show: function () {
            this._super();
            var order = this.pos.get_order();
            if (!order.is_to_invoice() && this.pos.config.auto_invoice) {
                this.click_invoice();
            }
        },
    });

});
