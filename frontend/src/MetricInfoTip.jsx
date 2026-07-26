import { useLayoutEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'

/**
 * Hover / keyboard-focus help tip with viewport-aware placement.
 * Pass { numerator, denominator } for a ratio fraction, and/or { formula } for a freeform equation.
 */
export default function MetricInfoTip({
  title,
  blurb,
  numerator,
  denominator,
  formula,
  ariaLabel,
  /** 'below' | 'above' | 'auto' — default auto; use below near top of viewport */
  placement = 'auto',
}) {
  const btnRef = useRef(null)
  const [open, setOpen] = useState(false)
  const [coords, setCoords] = useState(null)

  const hasFraction = numerator != null && denominator != null

  const updatePlace = () => {
    if (!btnRef.current) return
    const rect = btnRef.current.getBoundingClientRect()
    const width = Math.min(340, window.innerWidth - 24)
    let left = rect.left + rect.width / 2 - width / 2
    left = Math.max(12, Math.min(left, window.innerWidth - width - 12))
    const gap = 10
    const spaceAbove = rect.top
    const spaceBelow = window.innerHeight - rect.bottom
    // Tall blurbs need ~200px; prefer below unless forced above or clearly more room above.
    let placeAbove = false
    if (placement === 'above') placeAbove = true
    else if (placement === 'below') placeAbove = false
    else placeAbove = spaceAbove > spaceBelow && spaceAbove > 220

    if (placeAbove) {
      setCoords({
        width,
        left,
        bottom: window.innerHeight - rect.top + gap,
        top: undefined,
        placeAbove: true,
      })
    } else {
      setCoords({
        width,
        left,
        top: rect.bottom + gap,
        bottom: undefined,
        placeAbove: false,
      })
    }
  }

  useLayoutEffect(() => {
    if (!open) return undefined
    updatePlace()
    window.addEventListener('scroll', updatePlace, true)
    window.addEventListener('resize', updatePlace)
    return () => {
      window.removeEventListener('scroll', updatePlace, true)
      window.removeEventListener('resize', updatePlace)
    }
  }, [open, placement])

  if (!title) return null

  const show = () => {
    updatePlace()
    setOpen(true)
  }
  const hide = () => {
    setOpen(false)
    setCoords(null)
  }

  const pop = open && coords
    ? createPortal(
        <div
          className={`metric-info-pop is-open${coords.placeAbove ? ' is-above' : ' is-below'}`}
          role="tooltip"
          style={{
            top: coords.top,
            bottom: coords.bottom,
            left: coords.left,
            width: coords.width,
          }}
        >
          <span className="metric-info-head">
            <span className="metric-info-badge" aria-hidden="true">
              <svg viewBox="0 0 32 32" width="22" height="22">
                <rect x="6" y="8" width="14" height="16" rx="2" fill="#367ea2" />
                <rect x="9" y="11" width="8" height="2" rx="1" fill="#c9dfea" />
                <rect x="9" y="15" width="8" height="2" rx="1" fill="#c9dfea" />
                <rect x="9" y="19" width="5" height="2" rx="1" fill="#c9dfea" />
                <circle cx="22" cy="20" r="5" fill="#b1dff6" />
                <circle cx="22" cy="20" r="3.2" fill="#164654" />
              </svg>
            </span>
            {hasFraction ? (
              <>
                <span className="metric-info-title">{title}</span>
                <span className="metric-info-eq" aria-hidden="true">=</span>
                <span className="metric-info-frac">
                  <span className="metric-info-num">{numerator}</span>
                  <span className="metric-info-den">{denominator}</span>
                </span>
              </>
            ) : (
              <span className="metric-info-title metric-info-title-solo">{title}</span>
            )}
          </span>
          {formula ? (
            <span className="metric-info-formula">{formula}</span>
          ) : null}
          {blurb ? <span className="metric-info-body">{blurb}</span> : null}
        </div>,
        document.body,
      )
    : null

  return (
    <span
      className="metric-info"
      onMouseEnter={show}
      onMouseLeave={hide}
    >
      <button
        ref={btnRef}
        type="button"
        className="metric-info-btn"
        aria-label={ariaLabel || `Giải thích ${title}`}
        aria-expanded={open}
        onFocus={show}
        onBlur={hide}
      >
        i
      </button>
      {pop}
    </span>
  )
}
