// Auto-generated Cypher import script
// Generated: 2026-02-05T23:24:25.452790Z

// ============ NODES ============

// Bank nodes (2)
CREATE (:Bank {bank_id: "BANK_421", name: "Meridian Trust & Savings", country: "UK", regulatory_region: "FCA", source: "synthetic", created_at: "2026-02-05T23:22:36.270330Z", last_verified: "2026-02-05T23:22:36.270330Z", confidence: 1.0});
CREATE (:Bank {bank_id: "BANK_789", name: "Horizon Pacific International", country: "SG", regulatory_region: "MAS", source: "synthetic", created_at: "2026-02-05T23:22:36.270330Z", last_verified: "2026-02-05T23:22:36.270330Z", confidence: 1.0});

// Policy nodes (6)
CREATE (:Policy {policy_id: "AML_421_01", version: "v1", effective_from: "2024-01-01", policy_type: "AML", status: "active", bank_id: "BANK_421", source: "synthetic", created_at: "2026-02-05T23:22:49.322345Z", last_verified: "2026-02-05T23:22:49.322345Z", confidence: 1.0});
CREATE (:Policy {policy_id: "KYC_421_01", version: "v1", effective_from: "2024-01-01", policy_type: "KYC", status: "active", bank_id: "BANK_421", source: "synthetic", created_at: "2026-02-05T23:22:49.322345Z", last_verified: "2026-02-05T23:22:49.322345Z", confidence: 1.0});
CREATE (:Policy {policy_id: "FRAUD_421_01", version: "v1", effective_from: "2024-01-01", policy_type: "FRAUD", status: "active", bank_id: "BANK_421", source: "synthetic", created_at: "2026-02-05T23:22:49.322345Z", last_verified: "2026-02-05T23:22:49.322345Z", confidence: 1.0});
CREATE (:Policy {policy_id: "AML_101", version: "v1", effective_from: "2024-01-01", policy_type: "AML", status: "active", bank_id: "BANK_789", source: "synthetic", created_at: "2026-02-05T23:22:59.903817Z", last_verified: "2026-02-05T23:22:59.903817Z", confidence: 1.0});
CREATE (:Policy {policy_id: "KYC_202", version: "v1", effective_from: "2024-01-01", policy_type: "KYC", status: "active", bank_id: "BANK_789", source: "synthetic", created_at: "2026-02-05T23:22:59.903817Z", last_verified: "2026-02-05T23:22:59.903817Z", confidence: 1.0});
CREATE (:Policy {policy_id: "FRAUD_303", version: "v1", effective_from: "2024-01-01", policy_type: "FRAUD", status: "active", bank_id: "BANK_789", source: "synthetic", created_at: "2026-02-05T23:22:59.903817Z", last_verified: "2026-02-05T23:22:59.903817Z", confidence: 1.0});

// Rule nodes (12)
CREATE (:Rule {rule_id: "RULE_AML_001", policy_id: "AML_421_01", rule_type: "threshold", description: "Flag single cash deposits exceeding regulatory reporting limits", severity: "high", source: "synthetic", created_at: "2026-02-05T23:22:49.322345Z", last_verified: "2026-02-05T23:22:49.322345Z", confidence: 1.0});
CREATE (:Rule {rule_id: "RULE_AML_002", policy_id: "AML_421_01", rule_type: "conditional", description: "Monitor high-volume activity in newly opened accounts", severity: "medium", source: "synthetic", created_at: "2026-02-05T23:22:49.322345Z", last_verified: "2026-02-05T23:22:49.322345Z", confidence: 1.0});
CREATE (:Rule {rule_id: "RULE_KYC_001", policy_id: "KYC_421_01", rule_type: "conditional", description: "Require enhanced due diligence for customers in high-risk jurisdictions", severity: "high", source: "synthetic", created_at: "2026-02-05T23:22:49.322345Z", last_verified: "2026-02-05T23:22:49.322345Z", confidence: 1.0});
CREATE (:Rule {rule_id: "RULE_KYC_002", policy_id: "KYC_421_01", rule_type: "conditional", description: "Mandatory document refresh for corporate entities every 24 months", severity: "low", source: "synthetic", created_at: "2026-02-05T23:22:49.322345Z", last_verified: "2026-02-05T23:22:49.322345Z", confidence: 1.0});
CREATE (:Rule {rule_id: "RULE_FRAUD_001", policy_id: "FRAUD_421_01", rule_type: "threshold", description: "Detect unusual high-value outbound transfers", severity: "high", source: "synthetic", created_at: "2026-02-05T23:22:49.322345Z", last_verified: "2026-02-05T23:22:49.322345Z", confidence: 1.0});
CREATE (:Rule {rule_id: "RULE_FRAUD_002", policy_id: "FRAUD_421_01", rule_type: "conditional", description: "Block international wires from accounts less than 7 days old", severity: "high", source: "synthetic", created_at: "2026-02-05T23:22:49.322345Z", last_verified: "2026-02-05T23:22:49.322345Z", confidence: 1.0});
CREATE (:Rule {rule_id: "RULE_AML_001", policy_id: "AML_101", rule_type: "threshold", description: "Flag single transactions exceeding high-value reporting limits", severity: "high", source: "synthetic", created_at: "2026-02-05T23:22:59.903817Z", last_verified: "2026-02-05T23:22:59.903817Z", confidence: 1.0});
CREATE (:Rule {rule_id: "RULE_AML_002", policy_id: "AML_101", rule_type: "threshold", description: "Monitor daily cumulative volume for potential structuring", severity: "medium", source: "synthetic", created_at: "2026-02-05T23:22:59.903817Z", last_verified: "2026-02-05T23:22:59.903817Z", confidence: 1.0});
CREATE (:Rule {rule_id: "RULE_KYC_001", policy_id: "KYC_202", rule_type: "conditional", description: "Enhanced due diligence for Politically Exposed Persons", severity: "high", source: "synthetic", created_at: "2026-02-05T23:22:59.903817Z", last_verified: "2026-02-05T23:22:59.903817Z", confidence: 1.0});
CREATE (:Rule {rule_id: "RULE_KYC_002", policy_id: "KYC_202", rule_type: "conditional", description: "Restrict high-value operations for new accounts", severity: "medium", source: "synthetic", created_at: "2026-02-05T23:22:59.903817Z", last_verified: "2026-02-05T23:22:59.903817Z", confidence: 1.0});
CREATE (:Rule {rule_id: "RULE_FRD_001", policy_id: "FRAUD_303", rule_type: "threshold", description: "Detect rapid sequence of withdrawals (Velocity check)", severity: "high", source: "synthetic", created_at: "2026-02-05T23:22:59.903817Z", last_verified: "2026-02-05T23:22:59.903817Z", confidence: 1.0});
CREATE (:Rule {rule_id: "RULE_FRD_002", policy_id: "FRAUD_303", rule_type: "conditional", description: "Flag transactions from dormant accounts", severity: "high", source: "synthetic", created_at: "2026-02-05T23:22:59.903817Z", last_verified: "2026-02-05T23:22:59.903817Z", confidence: 1.0});

// Threshold nodes (6)
CREATE (:Threshold {threshold_id: "TH_AML_001", rule_id: "RULE_AML_001", metric: "transaction_amount", operator: ">=", value: 10000, currency: "USD", source: "synthetic", created_at: "2026-02-05T23:22:49.322345Z", last_verified: "2026-02-05T23:22:49.322345Z", confidence: 1.0});
CREATE (:Threshold {threshold_id: "TH_AML_002", rule_id: "RULE_AML_002", metric: "daily_volume", operator: ">", value: 25000, currency: "USD", source: "synthetic", created_at: "2026-02-05T23:22:49.322345Z", last_verified: "2026-02-05T23:22:49.322345Z", confidence: 1.0});
CREATE (:Threshold {threshold_id: "TH_FRD_001", rule_id: "RULE_FRAUD_001", metric: "transaction_amount", operator: ">", value: 50000, currency: "USD", source: "synthetic", created_at: "2026-02-05T23:22:49.322345Z", last_verified: "2026-02-05T23:22:49.322345Z", confidence: 1.0});
CREATE (:Threshold {threshold_id: "TH_AML_001", rule_id: "RULE_AML_001", metric: "transaction_amount", operator: ">=", value: 10000, currency: "USD", source: "synthetic", created_at: "2026-02-05T23:22:59.903817Z", last_verified: "2026-02-05T23:22:59.903817Z", confidence: 1.0});
CREATE (:Threshold {threshold_id: "TH_AML_002", rule_id: "RULE_AML_002", metric: "daily_volume", operator: ">", value: 50000, currency: "USD", source: "synthetic", created_at: "2026-02-05T23:22:59.903817Z", last_verified: "2026-02-05T23:22:59.903817Z", confidence: 1.0});
CREATE (:Threshold {threshold_id: "TH_FRD_001", rule_id: "RULE_FRD_001", metric: "hourly_withdrawal_count", operator: ">", value: 5, source: "synthetic", created_at: "2026-02-05T23:22:59.903817Z", last_verified: "2026-02-05T23:22:59.903817Z", confidence: 1.0});

// Condition nodes (9)
CREATE (:Condition {condition_id: "COND_AML_001", rule_id: "RULE_AML_002", field: "account_age_days", operator: "<", value: 30, source: "synthetic", created_at: "2026-02-05T23:22:49.322345Z", last_verified: "2026-02-05T23:22:49.322345Z", confidence: 1.0});
CREATE (:Condition {condition_id: "COND_KYC_001", rule_id: "RULE_KYC_001", field: "jurisdiction_risk_level", operator: "==", value: "high", source: "synthetic", created_at: "2026-02-05T23:22:49.322345Z", last_verified: "2026-02-05T23:22:49.322345Z", confidence: 1.0});
CREATE (:Condition {condition_id: "COND_KYC_002", rule_id: "RULE_KYC_002", field: "customer_type", operator: "==", value: "corporate", source: "synthetic", created_at: "2026-02-05T23:22:49.322345Z", last_verified: "2026-02-05T23:22:49.322345Z", confidence: 1.0});
CREATE (:Condition {condition_id: "COND_KYC_003", rule_id: "RULE_KYC_002", field: "days_since_last_kyc", operator: ">", value: 730, source: "synthetic", created_at: "2026-02-05T23:22:49.322345Z", last_verified: "2026-02-05T23:22:49.322345Z", confidence: 1.0});
CREATE (:Condition {condition_id: "COND_FRD_001", rule_id: "RULE_FRAUD_002", field: "account_age_days", operator: "<", value: 7, source: "synthetic", created_at: "2026-02-05T23:22:49.322345Z", last_verified: "2026-02-05T23:22:49.322345Z", confidence: 1.0});
CREATE (:Condition {condition_id: "COND_FRD_002", rule_id: "RULE_FRAUD_002", field: "transaction_type", operator: "==", value: "international_wire", source: "synthetic", created_at: "2026-02-05T23:22:49.322345Z", last_verified: "2026-02-05T23:22:49.322345Z", confidence: 1.0});
CREATE (:Condition {condition_id: "COND_KYC_001", rule_id: "RULE_KYC_001", field: "customer_type", operator: "==", value: "PEP", source: "synthetic", created_at: "2026-02-05T23:22:59.903817Z", last_verified: "2026-02-05T23:22:59.903817Z", confidence: 1.0});
CREATE (:Condition {condition_id: "COND_KYC_002", rule_id: "RULE_KYC_002", field: "account_age_days", operator: "<", value: 30, source: "synthetic", created_at: "2026-02-05T23:22:59.903817Z", last_verified: "2026-02-05T23:22:59.903817Z", confidence: 1.0});
CREATE (:Condition {condition_id: "COND_FRD_001", rule_id: "RULE_FRD_002", field: "account_status", operator: "==", value: "dormant", source: "synthetic", created_at: "2026-02-05T23:22:59.903817Z", last_verified: "2026-02-05T23:22:59.903817Z", confidence: 1.0});

// Customer nodes (5)
CREATE (:Customer {customer_id: "CUST_12845", bank_id: "BANK_789", risk_profile: "low", customer_type: "individual", source: "synthetic", created_at: "2026-02-05T23:23:20.040681Z", last_verified: "2026-02-05T23:23:20.040681Z", confidence: 1.0});
CREATE (:Customer {customer_id: "CUST_49201", bank_id: "BANK_789", risk_profile: "low", customer_type: "individual", source: "synthetic", created_at: "2026-02-05T23:23:20.040681Z", last_verified: "2026-02-05T23:23:20.040681Z", confidence: 1.0});
CREATE (:Customer {customer_id: "CUST_77312", bank_id: "BANK_789", risk_profile: "low", customer_type: "individual", source: "synthetic", created_at: "2026-02-05T23:23:20.040681Z", last_verified: "2026-02-05T23:23:20.040681Z", confidence: 1.0});
CREATE (:Customer {customer_id: "CUST_21094", bank_id: "BANK_789", risk_profile: "medium", customer_type: "individual", source: "synthetic", created_at: "2026-02-05T23:23:20.040681Z", last_verified: "2026-02-05T23:23:20.040681Z", confidence: 1.0});
CREATE (:Customer {customer_id: "CUST_99485", bank_id: "BANK_789", risk_profile: "high", customer_type: "business", source: "synthetic", created_at: "2026-02-05T23:23:20.040681Z", last_verified: "2026-02-05T23:23:20.040681Z", confidence: 1.0});

// Account nodes (7)
CREATE (:Account {account_id: "ACC_102938", customer_id: "CUST_12845", bank_id: "BANK_789", account_type: "savings", opened_on: "2021-03-12", status: "active", source: "synthetic", created_at: "2026-02-05T23:23:20.040681Z", last_verified: "2026-02-05T23:23:20.040681Z", confidence: 1.0});
CREATE (:Account {account_id: "ACC_102939", customer_id: "CUST_12845", bank_id: "BANK_789", account_type: "checking", opened_on: "2021-03-12", status: "active", source: "synthetic", created_at: "2026-02-05T23:23:20.040681Z", last_verified: "2026-02-05T23:23:20.040681Z", confidence: 1.0});
CREATE (:Account {account_id: "ACC_456281", customer_id: "CUST_49201", bank_id: "BANK_789", account_type: "checking", opened_on: "2023-11-20", status: "active", source: "synthetic", created_at: "2026-02-05T23:23:20.040681Z", last_verified: "2026-02-05T23:23:20.040681Z", confidence: 1.0});
CREATE (:Account {account_id: "ACC_882736", customer_id: "CUST_77312", bank_id: "BANK_789", account_type: "savings", opened_on: "2020-05-04", status: "active", source: "synthetic", created_at: "2026-02-05T23:23:20.040681Z", last_verified: "2026-02-05T23:23:20.040681Z", confidence: 1.0});
CREATE (:Account {account_id: "ACC_334219", customer_id: "CUST_21094", bank_id: "BANK_789", account_type: "checking", opened_on: "2022-08-15", status: "suspended", source: "synthetic", created_at: "2026-02-05T23:23:20.040681Z", last_verified: "2026-02-05T23:23:20.040681Z", confidence: 1.0});
CREATE (:Account {account_id: "ACC_334220", customer_id: "CUST_21094", bank_id: "BANK_789", account_type: "savings", opened_on: "2022-08-15", status: "active", source: "synthetic", created_at: "2026-02-05T23:23:20.040681Z", last_verified: "2026-02-05T23:23:20.040681Z", confidence: 1.0});
CREATE (:Account {account_id: "ACC_771822", customer_id: "CUST_99485", bank_id: "BANK_789", account_type: "business", opened_on: "2024-01-10", status: "active", source: "synthetic", created_at: "2026-02-05T23:23:20.040681Z", last_verified: "2026-02-05T23:23:20.040681Z", confidence: 1.0});

// Transaction nodes (15)
CREATE (:Transaction {transaction_id: "TXN_A1B2C3D4", account_id: "ACC_102938", customer_id: "CUST_12845", amount: 15400.0, currency: "INR", timestamp: "2023-10-15T14:20:00Z", channel: "online", transaction_type: "transfer", source: "synthetic", created_at: "2026-02-05T23:23:31.475650Z", last_verified: "2026-02-05T23:23:31.475650Z", confidence: 1.0});
CREATE (:Transaction {transaction_id: "TXN_E5F6G7H8", account_id: "ACC_102938", customer_id: "CUST_12845", amount: 5000.0, currency: "INR", timestamp: "2023-11-20T10:15:30Z", channel: "atm", transaction_type: "withdrawal", source: "synthetic", created_at: "2026-02-05T23:23:31.475650Z", last_verified: "2026-02-05T23:23:31.475650Z", confidence: 1.0});
CREATE (:Transaction {transaction_id: "TXN_Z9Y8X7W6", account_id: "ACC_102938", customer_id: "CUST_12845", amount: 1250000.0, currency: "INR", timestamp: "2023-12-05T09:00:00Z", channel: "international", transaction_type: "transfer", source: "synthetic", created_at: "2026-02-05T23:23:31.475650Z", last_verified: "2026-02-05T23:23:31.475650Z", confidence: 1.0});
CREATE (:Transaction {transaction_id: "TXN_A9B1C8D2", account_id: "ACC_456281", customer_id: "CUST_49201", amount: 12500.0, currency: "INR", timestamp: "2024-01-12T10:15:30Z", channel: "online", transaction_type: "transfer", source: "synthetic", created_at: "2026-02-05T23:23:50.629895Z", last_verified: "2026-02-05T23:23:50.629895Z", confidence: 1.0});
CREATE (:Transaction {transaction_id: "TXN_M4N7P2Q9", account_id: "ACC_456281", customer_id: "CUST_49201", amount: 1500000.0, currency: "INR", timestamp: "2024-02-25T14:45:00Z", channel: "international", transaction_type: "transfer", source: "synthetic", created_at: "2026-02-05T23:23:50.629895Z", last_verified: "2026-02-05T23:23:50.629895Z", confidence: 1.0});
CREATE (:Transaction {transaction_id: "TXN_X3Y6Z1W8", account_id: "ACC_456281", customer_id: "CUST_49201", amount: 5000.0, currency: "INR", timestamp: "2024-03-10T09:20:15Z", channel: "atm", transaction_type: "withdrawal", source: "synthetic", created_at: "2026-02-05T23:23:50.629895Z", last_verified: "2026-02-05T23:23:50.629895Z", confidence: 1.0});
CREATE (:Transaction {transaction_id: "TXN_A7B2C9D1", account_id: "ACC_882736", customer_id: "CUST_77312", amount: 4500.0, currency: "INR", timestamp: "2023-11-12T14:30:45Z", channel: "atm", transaction_type: "withdrawal", source: "synthetic", created_at: "2026-02-05T23:24:01.145599Z", last_verified: "2026-02-05T23:24:01.145599Z", confidence: 1.0});
CREATE (:Transaction {transaction_id: "TXN_K9L3M8N4", account_id: "ACC_882736", customer_id: "CUST_77312", amount: 1250000.0, currency: "INR", timestamp: "2024-01-05T09:15:20Z", channel: "international", transaction_type: "transfer", source: "synthetic", created_at: "2026-02-05T23:24:01.145599Z", last_verified: "2026-02-05T23:24:01.145599Z", confidence: 1.0});
CREATE (:Transaction {transaction_id: "TXN_P1Q5R2S9", account_id: "ACC_882736", customer_id: "CUST_77312", amount: 12500.5, currency: "INR", timestamp: "2024-02-14T18:45:10Z", channel: "online", transaction_type: "deposit", source: "synthetic", created_at: "2026-02-05T23:24:01.145599Z", last_verified: "2026-02-05T23:24:01.145599Z", confidence: 1.0});
CREATE (:Transaction {transaction_id: "TXN_A9B8C7D6", account_id: "ACC_334219", customer_id: "CUST_21094", amount: 25000.0, currency: "INR", timestamp: "2024-01-15T14:20:00Z", channel: "online", transaction_type: "transfer", source: "synthetic", created_at: "2026-02-05T23:24:10.768131Z", last_verified: "2026-02-05T23:24:10.768131Z", confidence: 1.0});
CREATE (:Transaction {transaction_id: "TXN_Z1Y2X3W4", account_id: "ACC_334219", customer_id: "CUST_21094", amount: 1500000.0, currency: "INR", timestamp: "2024-02-10T09:15:45Z", channel: "international", transaction_type: "transfer", source: "synthetic", created_at: "2026-02-05T23:24:10.768131Z", last_verified: "2026-02-05T23:24:10.768131Z", confidence: 1.0});
CREATE (:Transaction {transaction_id: "TXN_M5N4P3Q2", account_id: "ACC_334219", customer_id: "CUST_21094", amount: 500.0, currency: "USD", timestamp: "2024-03-01T18:30:00Z", channel: "atm", transaction_type: "withdrawal", source: "synthetic", created_at: "2026-02-05T23:24:10.768131Z", last_verified: "2026-02-05T23:24:10.768131Z", confidence: 1.0});
CREATE (:Transaction {transaction_id: "TXN_A7B2C9D1", account_id: "ACC_771822", customer_id: "CUST_99485", amount: 45000.0, currency: "INR", timestamp: "2023-11-14T10:30:00Z", channel: "branch", transaction_type: "deposit", source: "synthetic", created_at: "2026-02-05T23:24:23.811900Z", last_verified: "2026-02-05T23:24:23.811900Z", confidence: 1.0});
CREATE (:Transaction {transaction_id: "TXN_K8L3M4N5", account_id: "ACC_771822", customer_id: "CUST_99485", amount: 1250000.0, currency: "INR", timestamp: "2023-12-05T14:15:22Z", channel: "international", transaction_type: "transfer", source: "synthetic", created_at: "2026-02-05T23:24:23.811900Z", last_verified: "2026-02-05T23:24:23.811900Z", confidence: 1.0});
CREATE (:Transaction {transaction_id: "TXN_P1Q9R2S8", account_id: "ACC_771822", customer_id: "CUST_99485", amount: 12500.0, currency: "INR", timestamp: "2024-02-10T09:45:10Z", channel: "online", transaction_type: "transfer", source: "synthetic", created_at: "2026-02-05T23:24:23.811900Z", last_verified: "2026-02-05T23:24:23.811900Z", confidence: 1.0});

// RiskFlag nodes (5)
CREATE (:RiskFlag {risk_flag_id: "RF_5501", transaction_id: "TXN_Z9Y8X7W6", rule_id: "AML_101", flag_type: "manual_review", confidence: 1.0, source: "synthetic", created_at: "2026-02-05T23:23:31.475650Z", last_verified: "2026-02-05T23:23:31.475650Z"});
CREATE (:RiskFlag {risk_flag_id: "RF_8821", transaction_id: "TXN_M4N7P2Q9", rule_id: "AML_101", flag_type: "manual_review", confidence: 1.0, source: "synthetic", created_at: "2026-02-05T23:23:50.629895Z", last_verified: "2026-02-05T23:23:50.629895Z"});
CREATE (:RiskFlag {risk_flag_id: "RF_9921", transaction_id: "TXN_K9L3M8N4", rule_id: "AML_101", flag_type: "manual_review", confidence: 1.0, source: "synthetic", created_at: "2026-02-05T23:24:01.145599Z", last_verified: "2026-02-05T23:24:01.145599Z"});
CREATE (:RiskFlag {risk_flag_id: "RF_9021", transaction_id: "TXN_Z1Y2X3W4", rule_id: "AML_101", flag_type: "manual_review", confidence: 1.0, source: "synthetic", created_at: "2026-02-05T23:24:10.768131Z", last_verified: "2026-02-05T23:24:10.768131Z"});
CREATE (:RiskFlag {risk_flag_id: "RF_1001", transaction_id: "TXN_K8L3M4N5", rule_id: "AML_101", flag_type: "manual_review", confidence: 1.0, source: "synthetic", created_at: "2026-02-05T23:24:23.811900Z", last_verified: "2026-02-05T23:24:23.811900Z"});

// Decision nodes (15)
CREATE (:Decision {decision_id: "DEC_1001", transaction_id: "TXN_A1B2C3D4", decision_type: "approved", timestamp: "2023-10-15T14:20:02Z", source: "synthetic", created_at: "2026-02-05T23:23:31.475650Z", last_verified: "2026-02-05T23:23:31.475650Z", confidence: 1.0});
CREATE (:Decision {decision_id: "DEC_1002", transaction_id: "TXN_E5F6G7H8", decision_type: "approved", timestamp: "2023-11-20T10:15:32Z", source: "synthetic", created_at: "2026-02-05T23:23:31.475650Z", last_verified: "2026-02-05T23:23:31.475650Z", confidence: 1.0});
CREATE (:Decision {decision_id: "DEC_1003", transaction_id: "TXN_Z9Y8X7W6", decision_type: "flagged", reason: "High-value international transfer exceeding threshold for AML_101 compliance monitoring.", timestamp: "2023-12-05T09:00:05Z", source: "synthetic", created_at: "2026-02-05T23:23:31.475650Z", last_verified: "2026-02-05T23:23:31.475650Z", confidence: 1.0});
CREATE (:Decision {decision_id: "DEC_10001", transaction_id: "TXN_A9B1C8D2", decision_type: "approved", timestamp: "2024-01-12T10:15:32Z", source: "synthetic", created_at: "2026-02-05T23:23:50.629895Z", last_verified: "2026-02-05T23:23:50.629895Z", confidence: 1.0});
CREATE (:Decision {decision_id: "DEC_10002", transaction_id: "TXN_M4N7P2Q9", decision_type: "flagged", reason: "High value international transfer exceeding AML threshold", timestamp: "2024-02-25T14:45:10Z", source: "synthetic", created_at: "2026-02-05T23:23:50.629895Z", last_verified: "2026-02-05T23:23:50.629895Z", confidence: 1.0});
CREATE (:Decision {decision_id: "DEC_10003", transaction_id: "TXN_X3Y6Z1W8", decision_type: "approved", timestamp: "2024-03-10T09:20:18Z", source: "synthetic", created_at: "2026-02-05T23:23:50.629895Z", last_verified: "2026-02-05T23:23:50.629895Z", confidence: 1.0});
CREATE (:Decision {decision_id: "DEC_55001", transaction_id: "TXN_A7B2C9D1", decision_type: "approved", timestamp: "2023-11-12T14:30:47Z", source: "synthetic", created_at: "2026-02-05T23:24:01.145599Z", last_verified: "2026-02-05T23:24:01.145599Z", confidence: 1.0});
CREATE (:Decision {decision_id: "DEC_55002", transaction_id: "TXN_K9L3M8N4", decision_type: "flagged", reason: "Transaction amount exceeds 1,000,000 INR threshold via international channel", timestamp: "2024-01-05T09:15:25Z", source: "synthetic", created_at: "2026-02-05T23:24:01.145599Z", last_verified: "2026-02-05T23:24:01.145599Z", confidence: 1.0});
CREATE (:Decision {decision_id: "DEC_55003", transaction_id: "TXN_P1Q5R2S9", decision_type: "approved", timestamp: "2024-02-14T18:45:12Z", source: "synthetic", created_at: "2026-02-05T23:24:01.145599Z", last_verified: "2026-02-05T23:24:01.145599Z", confidence: 1.0});
CREATE (:Decision {decision_id: "DEC_10001", transaction_id: "TXN_A9B8C7D6", decision_type: "approved", timestamp: "2024-01-15T14:20:02Z", source: "synthetic", created_at: "2026-02-05T23:24:10.768131Z", last_verified: "2026-02-05T23:24:10.768131Z", confidence: 1.0});
CREATE (:Decision {decision_id: "DEC_10002", transaction_id: "TXN_Z1Y2X3W4", decision_type: "flagged", reason: "Transaction exceeds 1,000,000 INR limit and involves international channel.", timestamp: "2024-02-10T09:15:50Z", source: "synthetic", created_at: "2026-02-05T23:24:10.768131Z", last_verified: "2026-02-05T23:24:10.768131Z", confidence: 1.0});
CREATE (:Decision {decision_id: "DEC_10003", transaction_id: "TXN_M5N4P3Q2", decision_type: "approved", timestamp: "2024-03-01T18:30:05Z", source: "synthetic", created_at: "2026-02-05T23:24:10.768131Z", last_verified: "2026-02-05T23:24:10.768131Z", confidence: 1.0});
CREATE (:Decision {decision_id: "DEC_50001", transaction_id: "TXN_A7B2C9D1", decision_type: "approved", timestamp: "2023-11-14T10:30:05Z", source: "synthetic", created_at: "2026-02-05T23:24:23.811900Z", last_verified: "2026-02-05T23:24:23.811900Z", confidence: 1.0});
CREATE (:Decision {decision_id: "DEC_50002", transaction_id: "TXN_K8L3M4N5", decision_type: "flagged", reason: "High value international transfer exceeding AML threshold", timestamp: "2023-12-05T14:15:30Z", source: "synthetic", created_at: "2026-02-05T23:24:23.811900Z", last_verified: "2026-02-05T23:24:23.811900Z", confidence: 1.0});
CREATE (:Decision {decision_id: "DEC_50003", transaction_id: "TXN_P1Q9R2S8", decision_type: "approved", timestamp: "2024-02-10T09:45:12Z", source: "synthetic", created_at: "2026-02-05T23:24:23.811900Z", last_verified: "2026-02-05T23:24:23.811900Z", confidence: 1.0});

// ============ RELATIONSHIPS ============

// OWNS_ACCOUNT (7)
MATCH (a:Customer {customer_id: "CUST_12845"}), (b:Account {account_id: "ACC_102938"}) CREATE (a)-[:OWNS_ACCOUNT]->(b);
MATCH (a:Customer {customer_id: "CUST_12845"}), (b:Account {account_id: "ACC_102939"}) CREATE (a)-[:OWNS_ACCOUNT]->(b);
MATCH (a:Customer {customer_id: "CUST_49201"}), (b:Account {account_id: "ACC_456281"}) CREATE (a)-[:OWNS_ACCOUNT]->(b);
MATCH (a:Customer {customer_id: "CUST_77312"}), (b:Account {account_id: "ACC_882736"}) CREATE (a)-[:OWNS_ACCOUNT]->(b);
MATCH (a:Customer {customer_id: "CUST_21094"}), (b:Account {account_id: "ACC_334219"}) CREATE (a)-[:OWNS_ACCOUNT]->(b);
MATCH (a:Customer {customer_id: "CUST_21094"}), (b:Account {account_id: "ACC_334220"}) CREATE (a)-[:OWNS_ACCOUNT]->(b);
MATCH (a:Customer {customer_id: "CUST_99485"}), (b:Account {account_id: "ACC_771822"}) CREATE (a)-[:OWNS_ACCOUNT]->(b);

// OPERATES (7)
MATCH (a:Bank {bank_id: "BANK_789"}), (b:Account {account_id: "ACC_102938"}) CREATE (a)-[:OPERATES]->(b);
MATCH (a:Bank {bank_id: "BANK_789"}), (b:Account {account_id: "ACC_102939"}) CREATE (a)-[:OPERATES]->(b);
MATCH (a:Bank {bank_id: "BANK_789"}), (b:Account {account_id: "ACC_456281"}) CREATE (a)-[:OPERATES]->(b);
MATCH (a:Bank {bank_id: "BANK_789"}), (b:Account {account_id: "ACC_882736"}) CREATE (a)-[:OPERATES]->(b);
MATCH (a:Bank {bank_id: "BANK_789"}), (b:Account {account_id: "ACC_334219"}) CREATE (a)-[:OPERATES]->(b);
MATCH (a:Bank {bank_id: "BANK_789"}), (b:Account {account_id: "ACC_334220"}) CREATE (a)-[:OPERATES]->(b);
MATCH (a:Bank {bank_id: "BANK_789"}), (b:Account {account_id: "ACC_771822"}) CREATE (a)-[:OPERATES]->(b);

// EXECUTED_ON (15)
MATCH (a:Transaction {transaction_id: "TXN_A1B2C3D4"}), (b:Account {account_id: "ACC_102938"}) CREATE (a)-[:EXECUTED_ON]->(b);
MATCH (a:Transaction {transaction_id: "TXN_E5F6G7H8"}), (b:Account {account_id: "ACC_102938"}) CREATE (a)-[:EXECUTED_ON]->(b);
MATCH (a:Transaction {transaction_id: "TXN_Z9Y8X7W6"}), (b:Account {account_id: "ACC_102938"}) CREATE (a)-[:EXECUTED_ON]->(b);
MATCH (a:Transaction {transaction_id: "TXN_A9B1C8D2"}), (b:Account {account_id: "ACC_456281"}) CREATE (a)-[:EXECUTED_ON]->(b);
MATCH (a:Transaction {transaction_id: "TXN_M4N7P2Q9"}), (b:Account {account_id: "ACC_456281"}) CREATE (a)-[:EXECUTED_ON]->(b);
MATCH (a:Transaction {transaction_id: "TXN_X3Y6Z1W8"}), (b:Account {account_id: "ACC_456281"}) CREATE (a)-[:EXECUTED_ON]->(b);
MATCH (a:Transaction {transaction_id: "TXN_A7B2C9D1"}), (b:Account {account_id: "ACC_882736"}) CREATE (a)-[:EXECUTED_ON]->(b);
MATCH (a:Transaction {transaction_id: "TXN_K9L3M8N4"}), (b:Account {account_id: "ACC_882736"}) CREATE (a)-[:EXECUTED_ON]->(b);
MATCH (a:Transaction {transaction_id: "TXN_P1Q5R2S9"}), (b:Account {account_id: "ACC_882736"}) CREATE (a)-[:EXECUTED_ON]->(b);
MATCH (a:Transaction {transaction_id: "TXN_A9B8C7D6"}), (b:Account {account_id: "ACC_334219"}) CREATE (a)-[:EXECUTED_ON]->(b);
MATCH (a:Transaction {transaction_id: "TXN_Z1Y2X3W4"}), (b:Account {account_id: "ACC_334219"}) CREATE (a)-[:EXECUTED_ON]->(b);
MATCH (a:Transaction {transaction_id: "TXN_M5N4P3Q2"}), (b:Account {account_id: "ACC_334219"}) CREATE (a)-[:EXECUTED_ON]->(b);
MATCH (a:Transaction {transaction_id: "TXN_A7B2C9D1"}), (b:Account {account_id: "ACC_771822"}) CREATE (a)-[:EXECUTED_ON]->(b);
MATCH (a:Transaction {transaction_id: "TXN_K8L3M4N5"}), (b:Account {account_id: "ACC_771822"}) CREATE (a)-[:EXECUTED_ON]->(b);
MATCH (a:Transaction {transaction_id: "TXN_P1Q9R2S8"}), (b:Account {account_id: "ACC_771822"}) CREATE (a)-[:EXECUTED_ON]->(b);

// INITIATED_BY (15)
MATCH (a:Transaction {transaction_id: "TXN_A1B2C3D4"}), (b:Customer {customer_id: "CUST_12845"}) CREATE (a)-[:INITIATED_BY]->(b);
MATCH (a:Transaction {transaction_id: "TXN_E5F6G7H8"}), (b:Customer {customer_id: "CUST_12845"}) CREATE (a)-[:INITIATED_BY]->(b);
MATCH (a:Transaction {transaction_id: "TXN_Z9Y8X7W6"}), (b:Customer {customer_id: "CUST_12845"}) CREATE (a)-[:INITIATED_BY]->(b);
MATCH (a:Transaction {transaction_id: "TXN_A9B1C8D2"}), (b:Customer {customer_id: "CUST_49201"}) CREATE (a)-[:INITIATED_BY]->(b);
MATCH (a:Transaction {transaction_id: "TXN_M4N7P2Q9"}), (b:Customer {customer_id: "CUST_49201"}) CREATE (a)-[:INITIATED_BY]->(b);
MATCH (a:Transaction {transaction_id: "TXN_X3Y6Z1W8"}), (b:Customer {customer_id: "CUST_49201"}) CREATE (a)-[:INITIATED_BY]->(b);
MATCH (a:Transaction {transaction_id: "TXN_A7B2C9D1"}), (b:Customer {customer_id: "CUST_77312"}) CREATE (a)-[:INITIATED_BY]->(b);
MATCH (a:Transaction {transaction_id: "TXN_K9L3M8N4"}), (b:Customer {customer_id: "CUST_77312"}) CREATE (a)-[:INITIATED_BY]->(b);
MATCH (a:Transaction {transaction_id: "TXN_P1Q5R2S9"}), (b:Customer {customer_id: "CUST_77312"}) CREATE (a)-[:INITIATED_BY]->(b);
MATCH (a:Transaction {transaction_id: "TXN_A9B8C7D6"}), (b:Customer {customer_id: "CUST_21094"}) CREATE (a)-[:INITIATED_BY]->(b);
MATCH (a:Transaction {transaction_id: "TXN_Z1Y2X3W4"}), (b:Customer {customer_id: "CUST_21094"}) CREATE (a)-[:INITIATED_BY]->(b);
MATCH (a:Transaction {transaction_id: "TXN_M5N4P3Q2"}), (b:Customer {customer_id: "CUST_21094"}) CREATE (a)-[:INITIATED_BY]->(b);
MATCH (a:Transaction {transaction_id: "TXN_A7B2C9D1"}), (b:Customer {customer_id: "CUST_99485"}) CREATE (a)-[:INITIATED_BY]->(b);
MATCH (a:Transaction {transaction_id: "TXN_K8L3M4N5"}), (b:Customer {customer_id: "CUST_99485"}) CREATE (a)-[:INITIATED_BY]->(b);
MATCH (a:Transaction {transaction_id: "TXN_P1Q9R2S8"}), (b:Customer {customer_id: "CUST_99485"}) CREATE (a)-[:INITIATED_BY]->(b);

// HAS_POLICY (6)
MATCH (a:Bank {bank_id: "BANK_421"}), (b:Policy {policy_id: "AML_421_01"}) CREATE (a)-[:HAS_POLICY]->(b);
MATCH (a:Bank {bank_id: "BANK_421"}), (b:Policy {policy_id: "KYC_421_01"}) CREATE (a)-[:HAS_POLICY]->(b);
MATCH (a:Bank {bank_id: "BANK_421"}), (b:Policy {policy_id: "FRAUD_421_01"}) CREATE (a)-[:HAS_POLICY]->(b);
MATCH (a:Bank {bank_id: "BANK_789"}), (b:Policy {policy_id: "AML_101"}) CREATE (a)-[:HAS_POLICY]->(b);
MATCH (a:Bank {bank_id: "BANK_789"}), (b:Policy {policy_id: "KYC_202"}) CREATE (a)-[:HAS_POLICY]->(b);
MATCH (a:Bank {bank_id: "BANK_789"}), (b:Policy {policy_id: "FRAUD_303"}) CREATE (a)-[:HAS_POLICY]->(b);

// CONTAINS_RULE (12)
MATCH (a:Policy {policy_id: "AML_421_01"}), (b:Rule {rule_id: "RULE_AML_001"}) CREATE (a)-[:CONTAINS_RULE]->(b);
MATCH (a:Policy {policy_id: "AML_421_01"}), (b:Rule {rule_id: "RULE_AML_002"}) CREATE (a)-[:CONTAINS_RULE]->(b);
MATCH (a:Policy {policy_id: "KYC_421_01"}), (b:Rule {rule_id: "RULE_KYC_001"}) CREATE (a)-[:CONTAINS_RULE]->(b);
MATCH (a:Policy {policy_id: "KYC_421_01"}), (b:Rule {rule_id: "RULE_KYC_002"}) CREATE (a)-[:CONTAINS_RULE]->(b);
MATCH (a:Policy {policy_id: "FRAUD_421_01"}), (b:Rule {rule_id: "RULE_FRAUD_001"}) CREATE (a)-[:CONTAINS_RULE]->(b);
MATCH (a:Policy {policy_id: "FRAUD_421_01"}), (b:Rule {rule_id: "RULE_FRAUD_002"}) CREATE (a)-[:CONTAINS_RULE]->(b);
MATCH (a:Policy {policy_id: "AML_101"}), (b:Rule {rule_id: "RULE_AML_001"}) CREATE (a)-[:CONTAINS_RULE]->(b);
MATCH (a:Policy {policy_id: "AML_101"}), (b:Rule {rule_id: "RULE_AML_002"}) CREATE (a)-[:CONTAINS_RULE]->(b);
MATCH (a:Policy {policy_id: "KYC_202"}), (b:Rule {rule_id: "RULE_KYC_001"}) CREATE (a)-[:CONTAINS_RULE]->(b);
MATCH (a:Policy {policy_id: "KYC_202"}), (b:Rule {rule_id: "RULE_KYC_002"}) CREATE (a)-[:CONTAINS_RULE]->(b);
MATCH (a:Policy {policy_id: "FRAUD_303"}), (b:Rule {rule_id: "RULE_FRD_001"}) CREATE (a)-[:CONTAINS_RULE]->(b);
MATCH (a:Policy {policy_id: "FRAUD_303"}), (b:Rule {rule_id: "RULE_FRD_002"}) CREATE (a)-[:CONTAINS_RULE]->(b);

// USES_THRESHOLD (6)
MATCH (a:Rule {rule_id: "RULE_AML_001"}), (b:Threshold {threshold_id: "TH_AML_001"}) CREATE (a)-[:USES_THRESHOLD]->(b);
MATCH (a:Rule {rule_id: "RULE_AML_002"}), (b:Threshold {threshold_id: "TH_AML_002"}) CREATE (a)-[:USES_THRESHOLD]->(b);
MATCH (a:Rule {rule_id: "RULE_FRAUD_001"}), (b:Threshold {threshold_id: "TH_FRD_001"}) CREATE (a)-[:USES_THRESHOLD]->(b);
MATCH (a:Rule {rule_id: "RULE_AML_001"}), (b:Threshold {threshold_id: "TH_AML_001"}) CREATE (a)-[:USES_THRESHOLD]->(b);
MATCH (a:Rule {rule_id: "RULE_AML_002"}), (b:Threshold {threshold_id: "TH_AML_002"}) CREATE (a)-[:USES_THRESHOLD]->(b);
MATCH (a:Rule {rule_id: "RULE_FRD_001"}), (b:Threshold {threshold_id: "TH_FRD_001"}) CREATE (a)-[:USES_THRESHOLD]->(b);

// USES_CONDITION (9)
MATCH (a:Rule {rule_id: "RULE_AML_002"}), (b:Condition {condition_id: "COND_AML_001"}) CREATE (a)-[:USES_CONDITION]->(b);
MATCH (a:Rule {rule_id: "RULE_KYC_001"}), (b:Condition {condition_id: "COND_KYC_001"}) CREATE (a)-[:USES_CONDITION]->(b);
MATCH (a:Rule {rule_id: "RULE_KYC_002"}), (b:Condition {condition_id: "COND_KYC_002"}) CREATE (a)-[:USES_CONDITION]->(b);
MATCH (a:Rule {rule_id: "RULE_KYC_002"}), (b:Condition {condition_id: "COND_KYC_003"}) CREATE (a)-[:USES_CONDITION]->(b);
MATCH (a:Rule {rule_id: "RULE_FRAUD_002"}), (b:Condition {condition_id: "COND_FRD_001"}) CREATE (a)-[:USES_CONDITION]->(b);
MATCH (a:Rule {rule_id: "RULE_FRAUD_002"}), (b:Condition {condition_id: "COND_FRD_002"}) CREATE (a)-[:USES_CONDITION]->(b);
MATCH (a:Rule {rule_id: "RULE_KYC_001"}), (b:Condition {condition_id: "COND_KYC_001"}) CREATE (a)-[:USES_CONDITION]->(b);
MATCH (a:Rule {rule_id: "RULE_KYC_002"}), (b:Condition {condition_id: "COND_KYC_002"}) CREATE (a)-[:USES_CONDITION]->(b);
MATCH (a:Rule {rule_id: "RULE_FRD_002"}), (b:Condition {condition_id: "COND_FRD_001"}) CREATE (a)-[:USES_CONDITION]->(b);

// TRIGGERS (5)
MATCH (a:Rule {rule_id: "AML_101"}), (b:RiskFlag {riskflag_id: "RF_5501"}) CREATE (a)-[:TRIGGERS]->(b);
MATCH (a:Rule {rule_id: "AML_101"}), (b:RiskFlag {riskflag_id: "RF_8821"}) CREATE (a)-[:TRIGGERS]->(b);
MATCH (a:Rule {rule_id: "AML_101"}), (b:RiskFlag {riskflag_id: "RF_9921"}) CREATE (a)-[:TRIGGERS]->(b);
MATCH (a:Rule {rule_id: "AML_101"}), (b:RiskFlag {riskflag_id: "RF_9021"}) CREATE (a)-[:TRIGGERS]->(b);
MATCH (a:Rule {rule_id: "AML_101"}), (b:RiskFlag {riskflag_id: "RF_1001"}) CREATE (a)-[:TRIGGERS]->(b);

// RESULTS_IN (15)
MATCH (a:Transaction {transaction_id: "TXN_A1B2C3D4"}), (b:Decision {decision_id: "DEC_1001"}) CREATE (a)-[:RESULTS_IN]->(b);
MATCH (a:Transaction {transaction_id: "TXN_E5F6G7H8"}), (b:Decision {decision_id: "DEC_1002"}) CREATE (a)-[:RESULTS_IN]->(b);
MATCH (a:Transaction {transaction_id: "TXN_Z9Y8X7W6"}), (b:Decision {decision_id: "DEC_1003"}) CREATE (a)-[:RESULTS_IN]->(b);
MATCH (a:Transaction {transaction_id: "TXN_A9B1C8D2"}), (b:Decision {decision_id: "DEC_10001"}) CREATE (a)-[:RESULTS_IN]->(b);
MATCH (a:Transaction {transaction_id: "TXN_M4N7P2Q9"}), (b:Decision {decision_id: "DEC_10002"}) CREATE (a)-[:RESULTS_IN]->(b);
MATCH (a:Transaction {transaction_id: "TXN_X3Y6Z1W8"}), (b:Decision {decision_id: "DEC_10003"}) CREATE (a)-[:RESULTS_IN]->(b);
MATCH (a:Transaction {transaction_id: "TXN_A7B2C9D1"}), (b:Decision {decision_id: "DEC_55001"}) CREATE (a)-[:RESULTS_IN]->(b);
MATCH (a:Transaction {transaction_id: "TXN_K9L3M8N4"}), (b:Decision {decision_id: "DEC_55002"}) CREATE (a)-[:RESULTS_IN]->(b);
MATCH (a:Transaction {transaction_id: "TXN_P1Q5R2S9"}), (b:Decision {decision_id: "DEC_55003"}) CREATE (a)-[:RESULTS_IN]->(b);
MATCH (a:Transaction {transaction_id: "TXN_A9B8C7D6"}), (b:Decision {decision_id: "DEC_10001"}) CREATE (a)-[:RESULTS_IN]->(b);
MATCH (a:Transaction {transaction_id: "TXN_Z1Y2X3W4"}), (b:Decision {decision_id: "DEC_10002"}) CREATE (a)-[:RESULTS_IN]->(b);
MATCH (a:Transaction {transaction_id: "TXN_M5N4P3Q2"}), (b:Decision {decision_id: "DEC_10003"}) CREATE (a)-[:RESULTS_IN]->(b);
MATCH (a:Transaction {transaction_id: "TXN_A7B2C9D1"}), (b:Decision {decision_id: "DEC_50001"}) CREATE (a)-[:RESULTS_IN]->(b);
MATCH (a:Transaction {transaction_id: "TXN_K8L3M4N5"}), (b:Decision {decision_id: "DEC_50002"}) CREATE (a)-[:RESULTS_IN]->(b);
MATCH (a:Transaction {transaction_id: "TXN_P1Q9R2S8"}), (b:Decision {decision_id: "DEC_50003"}) CREATE (a)-[:RESULTS_IN]->(b);

