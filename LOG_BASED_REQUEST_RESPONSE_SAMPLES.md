# Log Based Spider Request/Response Samples

Source: Spider logs from May 7 / May 28 and Java Core connector code.

All customer/account values below are sanitized. The structure, field names, and response wrappers are kept from the logs.

Common method:

```text
POST
Content-Type: application/json
```

Common successful Spider response wrapper:

```json
{
  "code": 200,
  "message": "Approved",
  "data": {}
}
```

## 1. Login - Customer Details by CIF

Endpoint:

```text
/api/v1/customer-details-cid
```

Request:

```json
{
  "requiredAccountNumber": "121123123121",
  "transactionDetails": {
    "transactionDateTimeLocal": "20260507103554",
    "captureDate": "20260507"
  },
  "functionCode": "200",
  "field125": "CUSTID|100001",
  "processingCode": "370001",
  "accountDetails": {
    "accountNumber": "121123121"
  },
  "stan": "100151449830",
  "channelControllerId": "IDH",
  "acquirerId": "11111"
}
```

Response:

```json
{
  "code": 200,
  "message": "Approved",
  "data": {
    "cardNumber": "*********",
    "processingCode": "370001",
    "stan": "100151449830",
    "localTransactionDateTime": "20260507103554",
    "captureDate": "20260507",
    "acquirerId": "11111",
    "authId": "UNI000",
    "responseCode": "000",
    "accountBalance": {
      "ledgerBalance": "+0000000000000000",
      "availableBalance": "+0000000000000000",
      "floatBalance": "+0000000000000000",
      "FFDBalance": "+0000000000000000",
      "userDefinedBalance": "+0000000000000000",
      "balanceCurrencyCode": null,
      "fallbackTime": null
    },
    "requiredAccountNumber": "121123123121",
    "channelControllerId": "IDH",
    "privateReserved": {
      "customerName": "MOCK CUSTOMER",
      "finacleCoreCustomerId": "100001",
      "dateOfBirth": "1990-01-01",
      "customerNIC": ["900000000V"],
      "passportNumber": null,
      "openDate": "2026-02-25",
      "primaryBranchOfCustomer": "LK0010001",
      "accountManagerOfCustomer": "2000",
      "mobileNumber": ["94770000000"],
      "emailId": ["mock.customer@example.com"],
      "customerCommAddress1": "ADDRESS LINE 1",
      "customerCommAddress2": "ADDRESS LINE 2",
      "customerCommAddressCityCode": "",
      "customerCommAddressStateCode": "",
      "customerCommAddressPinCode": "",
      "customerCommAddressCountryCode": "LK",
      "customerSalutationCode": "MR",
      "customerStatus": "20",
      "exitStatus": "",
      "target": "120",
      "gender": "MALE",
      "sector": "8000"
    }
  }
}
```

## 2. Dashboard - Savings Account Details

Endpoint:

```text
/api/v1/savings-account-details
```

Request:

```json
{
  "requiredAccountNumber": "121123321121",
  "transactionDetails": {
    "transactionDateTimeLocal": "20260507103556",
    "captureDate": "20260507"
  },
  "functionCode": "200",
  "field125": {
    "pageNumberRequested": "1",
    "finacleCoreCustomerId": "100001",
    "accountType": "SBA",
    "recordsPerPage": "99"
  },
  "processingCode": "370000",
  "accountDetails": {
    "accountNumber": "123123123"
  },
  "stan": "100151449872",
  "channelControllerId": "IDH",
  "acquirerId": "11111"
}
```

Response:

```json
{
  "code": 200,
  "message": "Approved",
  "data": {
    "cardNumber": "*********",
    "processingCode": "370000",
    "stan": "100151449872",
    "localTransactionDateTime": "20260507103556",
    "captureDate": "20260507",
    "acquirerId": "11111",
    "authId": "UNI000",
    "responseCode": "000",
    "accountBalance": {
      "ledgerBalance": "+0000000000000000",
      "availableBalance": "+0000000000000000",
      "floatBalance": "+0000000000000000",
      "FFDBalance": "+0000000000000000",
      "userDefinedBalance": "+0000000000000000",
      "balanceCurrencyCode": null,
      "fallbackTime": null
    },
    "requiredAccountNumber": "121123321121",
    "channelControllerId": "IDH",
    "privateReserved": {
      "pageFetched": "LP",
      "numberOfRecordsInPage": "1",
      "finacleCoreCustomerId": "100001",
      "accountTypeRequested": "SBA",
      "accountDetailsInPage": [
        {
          "accountNumber": "102000000001",
          "typeOfAccount": "SAVING",
          "clearBalanceAmount": "116689.82",
          "accountCurrencyCode": "LKR",
          "jointCustomer": "100001",
          "jointCustomerRole": "OWNER",
          "jointCustShortName": "MOCK CUSTOMER",
          "branchId": "LK0010001",
          "lockedAmount": "0",
          "productId": "SA.SAVINGS.MEGABONUS.P",
          "accountType": "ACCOUNTS",
          "branchName": "MOCK BRANCH",
          "accountHolderName": "MOCK CUSTOMER",
          "arrNo": "AA2605651Q4R",
          "accountStatus": "AUTH",
          "floatBalance": "0",
          "productGroup": "Savings Account - LCY",
          "customerPostingRestrict": "N",
          "workingBalance": "116689.82",
          "RelatedParty": "N",
          "jointCustMobile": "94770000000",
          "jointCustomerDetails": []
        }
      ]
    }
  }
}
```

## 3. Dashboard - Current Account Details

Endpoint:

```text
/api/v1/current-account-details
```

Request:

```json
{
  "requiredAccountNumber": "121123321121",
  "transactionDetails": {
    "transactionDateTimeLocal": "20260507103609",
    "captureDate": "20260507"
  },
  "functionCode": "200",
  "field125": {
    "pageNumberRequested": "1",
    "finacleCoreCustomerId": "100001",
    "accountType": "CAA",
    "recordsPerPage": "99"
  },
  "processingCode": "370000",
  "accountDetails": {
    "accountNumber": "123123123"
  },
  "stan": "100151449991",
  "channelControllerId": "IDH",
  "acquirerId": "11111"
}
```

Response:

```json
{
  "code": 200,
  "message": "Approved",
  "data": {
    "cardNumber": "*********",
    "processingCode": "370000",
    "stan": "100151449991",
    "localTransactionDateTime": "20260507103609",
    "captureDate": "20260507",
    "acquirerId": "11111",
    "authId": "UNI000",
    "responseCode": "000",
    "requiredAccountNumber": "121123321121",
    "channelControllerId": "IDH",
    "privateReserved": {
      "pageFetched": "LP",
      "numberOfRecordsInPage": "1",
      "finacleCoreCustomerId": "100001",
      "accountTypeRequested": "CAA",
      "accountDetailsInPage": [
        {
          "accountNumber": "101000000001",
          "typeOfAccount": "CURRENT",
          "clearBalanceAmount": "13.93",
          "accountCurrencyCode": "LKR",
          "jointCustomer": "100001",
          "jointCustomerRole": "OWNER",
          "jointCusShortName": "MOCK CUSTOMER",
          "branchId": "LK0010001",
          "lockedAmount": "0",
          "prodGroup": "Current Account - LCY",
          "productId": "CA.CURRENT.P",
          "InternalAmount": "0.00",
          "accountType": "ACCOUNTS",
          "branchName": "MOCK BRANCH",
          "drawPower": "13.93",
          "accountHolderName": "MOCK CUSTOMER",
          "arrNo": "AA25218QWH7W",
          "accountStatus": "AUTH",
          "floatBalance": "0",
          "customerPostingRestrict": "N",
          "RelatedParty": "N",
          "jointCustMobile": "94770000000",
          "jointCustomerDetails": []
        }
      ]
    }
  }
}
```

No-record response also appears in logs:

```json
{
  "code": 400,
  "message": "No Records Found",
  "data": {
    "code": "E-02",
    "message": "No Records Found",
    "type": "BUSINESS"
  }
}
```

## 4. Balance - Savings Account Details

Same endpoint/request/response shape as dashboard savings:

```text
/api/v1/savings-account-details
```

The app can use the same `privateReserved.accountDetailsInPage[].clearBalanceAmount` / `workingBalance` fields for balance display.

## 5. Balance - Current Account Details

Same endpoint/request/response shape as dashboard current:

```text
/api/v1/current-account-details
```

The app can use the same `privateReserved.accountDetailsInPage[].drawPower` / `clearBalanceAmount` fields for balance display.

## 6. Account Detail

Endpoint:

```text
/api/v1/account-details
```

Request:

```json
{
  "requiredAccountNumber": "102000000001",
  "transactionDetails": {
    "transactionDateTimeLocal": "20260507103557",
    "captureDate": "20260507"
  },
  "functionCode": "200",
  "processingCode": "820000",
  "accountDetails": {
    "accountNumber": "123121123"
  },
  "stan": "100151449877",
  "channelControllerId": "IDH",
  "acquirerId": "11111"
}
```

Response:

```json
{
  "code": 200,
  "message": "Approved",
  "data": {
    "cardNumber": "*********",
    "processingCode": "820000",
    "stan": "100151449877",
    "localTransactionDateTime": "20260507103557",
    "captureDate": "20260507",
    "acquirerId": "11111",
    "authId": "UNI000",
    "responseCode": "000",
    "accountBalance": {
      "ledgerBalance": "+0000000000000000",
      "availableBalance": "372840.37",
      "floatBalance": "0",
      "FFDBalance": "+0000000000000000",
      "userDefinedBalance": "+0000000000000000",
      "balanceCurrencyCode": "LKR",
      "fallbackTime": null
    },
    "requiredAccountNumber": "102000000001",
    "channelControllerId": "IDH",
    "privateReserved": {
      "finacleCoreCustomerId": "100001",
      "customerNameFinacleCRM": "MOCK CUSTOMER",
      "customerNameFinacleCore": "MOCK CUSTOMER",
      "accountOpenDate": "20251016",
      "accountProductCode": "SA.SAVINGS.ALOKA.P",
      "typeOfAccount": "SAVING",
      "authStatus": "verified",
      "accountClosedDate": null,
      "accountStatusCode": "ACTIVE",
      "accountSolId": "LK0010001",
      "drawingPowerAmount": "372840.37",
      "lienAmount": "0",
      "jointHolderName1": null,
      "jointHolderName2": null,
      "jointHolderName3": null,
      "numberOfRelatedParties": "0",
      "relatedPartiesDetails": [],
      "postingRestriction": "",
      "customerPostingRestrict": ""
    },
    "arrangementId": "AA25289WZ1P2",
    "accountCurrency": "LKR",
    "onlineClearedBalance": "372840.37",
    "onlineActualBalance": "372840.37",
    "branchName": "MOCK BRANCH",
    "productGroup": "ACCOUNTS.LCY.SAVINGS",
    "ownershipType": "OWNER"
  }
}
```

## 7. CEFT Confirm

Endpoint:

```text
/api/v1/fund-transfer/cefts
```

Request:

```json
{
  "settlmentDate": "0507103600",
  "transactionDetails": {
    "dateLocal": "20260507",
    "amount": 460000,
    "transactionDateTimeGmt": "0507103600",
    "timeLocal": "103600"
  },
  "processingCode": "480000",
  "posDetails": {
    "pinEntryMode": null,
    "panEntryMode": null,
    "terminalId": "6013",
    "conditionCode": null
  },
  "EFTTLVData": {
    "reference": "mock-reference",
    "destinationBankCode": "6083",
    "destinationAccountHolderName": "DEST CUSTOMER",
    "creditReference": "",
    "originatingBankCode": "7454",
    "cardHolderAddress": "CUSTOMER ADDRESS",
    "debitReference": "mock-debit-reference",
    "cardHolderId": "100001",
    "destinationAccountNumber": "************",
    "transactionCode": "52",
    "cardOriginatingAccountHolderName": "SOURCE CUSTOMER",
    "cardholderAccount": "102000000001"
  },
  "additionalTerminalData": "",
  "rrn": "102612736444",
  "serviceCharge": 25,
  "isoHeader": "CEFTCT",
  "stan": "SYMF202605071036008592263",
  "captureDate": "0507103600",
  "acquirerId": "DIGITAL.BANKING",
  "merchantType": "6014",
  "object": {
    "transactionType": "1",
    "privateData": "0",
    "messageFormatVersion": "01",
    "channelType": "1",
    "applicationID": "001",
    "uniqueNumber": "SYMF202605071036008592263",
    "transactionDateAndTime": "0507103600"
  }
}
```

Response:

```json
{
  "code": 200,
  "message": "Approved or completed successfully",
  "data": {
    "processingCode": "",
    "stan": "SYMF202605281100451882588",
    "extStan": "009591",
    "settlementDate": "00-00",
    "captureDate": "00-00",
    "retrievalReferenceNumber": "1026148C1644",
    "responseCode": "00",
    "cardAcceptorLocation": null,
    "statusCheck": false
  }
}
```
