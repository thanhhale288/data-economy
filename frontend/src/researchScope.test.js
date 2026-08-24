import assert from 'node:assert/strict'
import { test } from 'node:test'
import {
  SHOW_DIGITAL_VA_UI,
  SHOW_IIP_ANOMALY_UI,
  SHOW_IIP_FORECAST_UI,
  SHOW_LISTING_VSIC_UI,
  SHOW_ML_LAB,
  SHOW_ML_MONITORING_UI,
  SHOW_MODEL_METRICS_UI,
} from './researchScope.js'

test('advisor demo freeze flags stay off (T01 / T01b)', () => {
  assert.equal(SHOW_DIGITAL_VA_UI, false)
  assert.equal(SHOW_IIP_FORECAST_UI, false)
  assert.equal(SHOW_ML_LAB, false)
  assert.equal(SHOW_MODEL_METRICS_UI, false)
  assert.equal(SHOW_IIP_ANOMALY_UI, false)
  assert.equal(SHOW_LISTING_VSIC_UI, false)
  assert.equal(SHOW_ML_MONITORING_UI, false)
})
