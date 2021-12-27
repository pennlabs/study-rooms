import React, { ReactNode } from 'react'
import s, { css, FlattenSimpleInterpolation } from 'styled-components'
import { Nav } from '@/components/styles/Nav'
import {
  maxWidth,
  minWidth,
  PHONE,
  TABLET,
  MAX_BODY_HEIGHT,
  DESKTOP,
} from '@/components/styles/sizes'

interface IRow {
  maxHeight?: string
  overflowY?: string
  margin?: string
  justifyContent?: string
}

export const Row = s.div<IRow>(
  ({
    maxHeight,
    overflowY,
    margin,
    justifyContent,
  }): FlattenSimpleInterpolation => css`
    display: flex;
    flex-direction: row;
    width: 100%;
    flex-wrap: wrap;
    max-height: ${maxHeight || 'none'};
    overflow-y: ${overflowY || 'hidden'};

    ${margin &&
    ` margin-left: -${margin};
      margin-right: -${margin};
      width: calc(100% + ${margin} + ${margin});`}

    ${justifyContent && `justify-content: ${justifyContent};`}
  `
)

const percent = (numCols: number): string => `${(numCols / 12) * 100}%`

interface IColWrapper {
  width?: string
  padding?: string
  maxHeight?: string
  minHeight?: string
  height?: string
  fullHeight?: boolean
  flex?: boolean
  alignItems?: string
  sm?: number
  offsetSm?: number
  md?: number
  offsetMd?: number
  lg?: number
  offsetLg?: number
  hideOnMobile?: boolean
  overflowY?: string
  overflowX?: string
}

const ColWrapper = s.div<IColWrapper>(
  ({
    width,
    padding,
    height,
    fullHeight,
    flex,
    alignItems,
    sm,
    offsetSm,
    md,
    offsetMd,
    lg,
    offsetLg,
    hideOnMobile,
    overflowY,
    overflowX,
  }) => css`
    flex: ${width ? 'none' : 1};
    width: ${width || 'auto'};
    padding: ${padding || 0};
    ${overflowY && `overflow-y: ${overflowY}`};
    ${overflowX && `overflow-x: ${overflowX}`};

    ${height && `height: ${height};`}

    ${flex && 'display: flex;'}
    ${alignItems && `align-items: ${alignItems};`}

    ${minWidth(PHONE)} {
      ${sm && `width: ${percent(sm)}; flex: none;`}
      ${offsetSm && `margin-left: ${percent(offsetSm)};`}
    }

    ${minWidth(TABLET)} {
      ${md && `width: ${percent(md)}; flex: none;`}
      ${offsetMd && `margin-left: ${percent(offsetMd)};`}
    }

    ${minWidth(DESKTOP)} {
      ${lg && `width: ${percent(lg)}; flex: none;`}
      ${offsetLg && `margin-left: ${percent(offsetLg)};`}
      ${fullHeight && `height: ${MAX_BODY_HEIGHT};`}
    }

    ${maxWidth(PHONE)} {
      ${hideOnMobile && 'display: none !important;'}
    }
  `
)

interface IColContainer {
  margin?: string
}

const ColContainer = s.div<IColContainer>(({ margin }) =>
  margin ? `margin-left: ${margin}; margin-right: ${margin};` : ''
)

export type ICol = {
  margin?: string
  children?: React.ReactNode | React.ReactNodeArray
  style?: React.CSSProperties
  hideOnMobile?: boolean
} & IColWrapper &
  IColContainer

export const Col = ({ margin, children, ...other }: ICol) => (
  <ColWrapper {...other}>
    {margin ? (
      <ColContainer margin={margin}>{children}</ColContainer>
    ) : (
      children
    )}
  </ColWrapper>
)

interface iGroupProps {
  horizontal?: boolean // defaults to vertical
  alignItems?: string
  justifyContent?: string
  margin?: string
  center?: boolean
  fullWidth?: boolean
}

/**
 * Div wrapper for a group of elements.
 */
export const Group = s.div<iGroupProps>(
  ({
    horizontal,
    alignItems,
    justifyContent,
    margin,
    center,
    fullWidth,
  }) => css`
    display: ${horizontal ? 'flex' : 'inline-block'};
    ${justifyContent && `justify-content: ${justifyContent};`}
    ${alignItems && `align-items: ${alignItems};`}
    ${margin && `margin: ${margin};`}
    ${center && 'margin: 0 auto;'}
    ${fullWidth && 'flex-grow: 1'}
  `
)

export const Container = ({ children }: { children: ReactNode }) => {
  return (
    <Group horizontal>
      <Nav />
      <Group fullWidth>{children}</Group>
    </Group>
  )
}
