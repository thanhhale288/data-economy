/**
 * Evol-1 T01 / T01b — hide unvalidated demo surfaces after audit 20–21/8.
 * Keep macro GSO (IIP, VA_C) and company/benchmark pages.
 *
 * Hide, do not delete: shop matcher / product categorizer / marketplace crawlers
 * stay frozen for evol-1 T03 / T05 / T14. IIP forecast/anomaly code stays until
 * a later cut, but must not appear on the advisor demo.
 */
export const SHOW_DIGITAL_VA_UI = false
export const SHOW_IIP_FORECAST_UI = false
export const SHOW_ML_LAB = false
export const SHOW_MODEL_METRICS_UI = false
/** Isolation Forest chip on Dashboard IIP chart (Task #73). */
export const SHOW_IIP_ANOMALY_UI = false
/** Product-name → VSIC column on company listing table (Task #74). */
export const SHOW_LISTING_VSIC_UI = false
/** Pipeline ML quality/drift panel (Tasks #63 / #72). */
export const SHOW_ML_MONITORING_UI = false
