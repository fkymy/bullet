import React from 'react'
import PropTypes from 'prop-types'
import Helmet from 'react-helmet'

import Header from '../components/Header'
import './index.css'

const TemplateWrapper = ({ children }) => (
  <div>
    <Helmet
      title="賃貸管理 | Smart賃貸"
      meta={[
        {
          name: 'description',
          content: 'Smart賃貸はスマートな賃貸管理によって家賃収入の最大化を目指す管理会社です。'
        },
        {
          name: 'keywords',
          content: '賃貸, 管理'
        },
      ]}
    />
    <Header />
    <div
      style={{
        margin: '0 auto',
        maxWidth: 960,
        padding: '0px 1.0875rem 1.45rem',
        paddingTop: 0,
      }}
    >
      {children()}
    </div>
  </div>
)

TemplateWrapper.propTypes = {
  children: PropTypes.func,
}

export default TemplateWrapper
