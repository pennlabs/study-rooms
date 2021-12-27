import React, { useContext } from 'react'
import s from 'styled-components'
import Link from 'next/link'
import { useRouter, NextRouter } from 'next/router'

import Logo from '@/components/header/Logo'
import { Text } from '@/components/styles/Text'
import { Button } from '@/components/styles/Buttons'
import { colors } from '@/components/styles/colors'
import { Group } from '@/components/styles/Layout'
import { maxWidth, NAV_HEIGHT, PHONE } from '@/components/styles/sizes'
import { AuthUserContext } from '@/utils/auth'

const NavStyle = s.nav`
  padding: 1rem 1.5rem 0rem 1.5rem;
  display: flex;
  width: 100%;
  max-height: ${NAV_HEIGHT};
  position: fixed;
  top: 0;
  left: 0;
  background: rgba(255, 255, 255, 0.9);
  align-items: center;
  justify-content: space-between;
  z-index: 100;
`

const NavSpace = s.div`
  width: 100%;
  height: ${NAV_HEIGHT};
`

const NavLinkWrapper = s.div`
  margin-right: 4rem;
  ${maxWidth(PHONE)} {
    margin-right: 0.5rem;
  }
`

const NavLink = ({ title, link }: { title: string; link?: string }) => (
  <NavLinkWrapper>
    <Link href={link || `/${title}`}>
      <a>
        <Text heading>{title}</Text>
      </a>
    </Link>
  </NavLinkWrapper>
)

const Nav = () => {
  const { user } = useContext(AuthUserContext)
  const router: NextRouter = useRouter()

  const LandingPageNav = () => (
    <>
      <NavLink title="Home" />
      <NavLink title="About" />
      <NavLink title="Tutorial" />
      <NavLink title="Team" />
    </>
  )

  return (
    <>
      <NavStyle>
        <Logo />
        <Group horizontal margin="0 0 0.5rem 0">
          {!user ? (
            <LandingPageNav />
          ) : (
            <NavLink title="Create" link="/polls/create" />
          )}
          <Link
            href={`/api/accounts/${user ? 'logout' : 'login'}/?next=${
              router.pathname
            }`}
          >
            <a>
              <Button color={colors.MEDIUM_BLUE}>
                {user ? 'Logout' : 'Login'}
              </Button>
            </a>
          </Link>
        </Group>
      </NavStyle>
      <NavSpace />
    </>
  )
}

export default Nav
