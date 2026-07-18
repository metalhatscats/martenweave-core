# Patch note: block implausible sales net values (fictional pilot data)

The fictional CRM sales order extract currently ships `order_total` instead of the
agreed `net_value` column (see ISS-SALES-ORDERS-MISSING-NET-VALUE). While the extract
is being re-delivered, add an additional reviewable outlier rule on
ATTR-SALES-NET-VALUE so implausible values are flagged once
MAP-CRM-ORDER-NET-VALUE-TO-VBAK-NETWR is unblocked and FEP-S4-VBAK-NETWR is loaded.

Scope hint: create a new ValidationRule for ATTR-SALES-NET-VALUE in DOMAIN-SALES.
All data in this pilot is fictional and synthetic.
