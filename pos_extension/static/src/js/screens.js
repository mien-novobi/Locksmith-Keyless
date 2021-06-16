odoo.define('pos_extension.screens', function (require) {
    "use strict";

    var core = require('web.core');
    var screens = require('point_of_sale.screens');


    var _t = core._t;

    var PaymentScreenWidget = screens.PaymentScreenWidget;

    PaymentScreenWidget.include({
        click_sms: function () {
            var order = this.pos.get_order();
            order.set_to_sms(!order.is_to_sms());
            this.$('.js_sms').toggleClass('highlight', order.is_to_sms());
        },
        renderElement: function () {
            var self = this;
            this._super();

            this.$('.js_sms').click(function () {
                self.click_sms();
            });
        },
        order_is_valid: function (force_validation) {
            var self = this;

            var order = this.pos.get_order();
            var client = order.get_client();

            if (order.is_to_sms() && (!client || !(client.mobile || client.phone))) {
                var title = !client ?
                    _t('Please select the customer') :
                    _t('Please provide valid Mobile Number');
                var body = !client ?
                    _t('You need to select the customer before you can send the SMS.') :
                    _t('This customer does not have a valid mobile number, define one or do not send an SMS.');
                this.gui.show_popup('confirm', {
                    'title': title,
                    'body': body,
                    confirm: function () {
                        this.gui.show_screen('clientlist');
                    },
                });
                return false;
            }

            return this._super(force_validation);
        },
    });

});
