import xmlrpclib
uname="admin"
pwd="qplazm1092"
db='shipstation'

execute_sock=xmlrpclib.ServerProxy('http://localhost:10010/xmlrpc/object') # IMP
#resourse = 'https://ssapi11.shipstation.com/shipments?batchId=35321850&includeShipmentItems=True'
#resourse = 'https://ssapi11.shipstation.com/shipments?orderId=143605867&includeShipmentItems=False'
#res = execute_sock.execute(db, 1, pwd,'sale.order','import_order_from_webhook_notification', [], resourse,1)

shipment =[
    {
      "shipmentId": 33974374,
      "orderId": 140069422,
      "orderKey": "8061c220f0794a9b92460b8bae6837e4",
      "userId": "123456AB-ab12-3c4d-5e67-89f1abc1defa",
      "orderNumber": "100038-1",
      "createDate": "2014-10-03T06:51:33.6270000",
      "shipDate": "2014-10-03",
      "shipmentCost": 1.93,
      "insuranceCost": 0,
      "trackingNumber": "9400111899561704681189",
      "isReturnLabel": False,
      "batchNumber": "100301",
      "carrierCode": "stamps_com",
      "serviceCode": "usps_first_class_mail",
      "packageCode": "package",
      "confirmation": "delivery",
      "warehouseId": 16079,
      "voided": False,
      "voidDate": 'null',
      "marketplaceNotified": True,
      "notifyErrorMessage": 'null',
      "shipTo": {
        "name": "Yoda",
        "company": "",
        "street1": "12223 LOWDEN LN",
        "street2": "",
        "street3": 'null',
        "city": "MANCHACA",
        "state": "TX",
        "postalCode": "78652-3602",
        "country": "US",
        "phone": "2101235544",
        "residential": 'null'
      },
      "weight": {
        "value": 1,
        "units": "ounces"
      },
      "dimensions": 'null',
      "insuranceOptions": {
        "provider": 'null',
        "insureShipment": False,
        "insuredValue": 0
      },
      "advancedOptions": 'null',
      "shipmentItems": [
        {
          "orderItemId": 56568665,
          "lineItemKey": 'null',
          "sku": "SQ3785739",
          "name": "Potato Kitten -",
          "imageUrl": 'null',
          "weight": 'null',
          "quantity": 1,
          "unitPrice": 1,
          "warehouseLocation": 'null',
          "options": 'null',
          "productId": 7565777,
          "fulfillmentSku": 'null'
        }
      ],
      "labelData": 'null',
      "formData": 'null'
    },
    {
      "shipmentId": 33974373,
      "orderId": 43337328,
      "userId": "123456AB-ab12-3c4d-5e67-89f1abc1defa",
      "orderNumber": "100028",
      "createDate": "2014-10-03T06:51:59.9430000",
      "shipDate": "2014-10-03",
      "shipmentCost": 1.93,
      "insuranceCost": 0,
      "trackingNumber": "9400111899561704681196",
      "isReturnLabel": False,
      "batchNumber": "100300",
      "carrierCode": "stamps_com",
      "serviceCode": "usps_first_class_mail",
      "packageCode": "package",
      "confirmation": "delivery",
      "warehouseId": 14265,
      "voided": False,
      "voidDate": 'null',
      "marketplaceNotified": True,
      "notifyErrorMessage": 'null',
      "shipTo": {
        "name": "Luke Skywalker",
        "company": "SS",
        "street1": "2815 EXPOSITION BLVD",
        "street2": "",
        "street3": 'null',
        "city": "AUSTIN",
        "state": "TX",
        "postalCode": "78703-1221",
        "country": "US",
        "phone": "",
        "residential": 'null'
      },
      "weight": {
        "value": 1,
        "units": "ounces"
      },
      "dimensions": 'null',
      "insuranceOptions": {
        "provider": 'null',
        "insureShipment": False,
        "insuredValue": 0
      },
      "advancedOptions": 'null',
      "shipmentItems": [
        {
          "orderItemId": 55827278,
          "lineItemKey": 'null',
          "sku": "test",
          "name": "test",
          "imageUrl": 'null',
          "weight": 'null',
          "quantity": 1,
          "unitPrice": 1,
          "warehouseLocation": 'null',
          "options": 'null',
          "productId": 7541107,
          "fulfillmentSku": 'null'
        }
      ],
      "labelData": 'null',
      "formData": 'null'
    }
  ]

res = execute_sock.execute(db, 1, pwd,'sale.order','update_shipstation_order', [], shipment, 1)



print res


