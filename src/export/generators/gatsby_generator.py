"""
Gatsby Generator

CLAUDE.md Implementation:
- #3.4: Modern Gatsby patterns with static site generation
- #1.2: DRY component generation
- #4.1: TypeScript support
- #7.2: XSS prevention in templates
"""

import logging
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from pathlib import Path
import json
import re

from ..export_context import ExportContext
from ..export_config import ExportConfig
from .base_generator import BaseGenerator
from ...models.component_enhanced import Component

logger = logging.getLogger(__name__)


@dataclass
class GatsbyPageInfo:
    """Information about a Gatsby page"""
    component: Component
    name: str
    path: str
    slug: str
    template: str
    data_source: Optional[str] = None
    graphql_query: Optional[str] = None
    is_dynamic: bool = False


class GatsbyGenerator(BaseGenerator):
    """
    Generate modern Gatsby static site with React
    
    CLAUDE.md Implementation:
    - #3.4: Modern Gatsby patterns (GraphQL, static generation)
    - #1.2: DRY component generation
    """
    
    def __init__(self):
        super().__init__()
        self.page_registry: Dict[str, GatsbyPageInfo] = {}
        self.generated_queries: Set[str] = set()
        
    async def generate(self, context: ExportContext) -> Dict[str, str]:
        """Generate complete Gatsby application"""
        files = {}
        config = context.config.options
        
        # Generate package.json
        files["package.json"] = self._generate_package_json(context)
        
        # Generate Gatsby config files
        files["gatsby-config.js"] = self._generate_gatsby_config(context)
        files["gatsby-node.js"] = self._generate_gatsby_node(context)
        files["gatsby-browser.js"] = self._generate_gatsby_browser(context)
        files["gatsby-ssr.js"] = self._generate_gatsby_ssr(context)
        
        # Generate TypeScript config if enabled
        if config.use_typescript:
            files["tsconfig.json"] = self._generate_tsconfig()
        
        # Generate main layout and pages
        layout_files = await self._generate_layouts(context)
        files.update(layout_files)
        
        # Generate pages from components
        page_files = await self._generate_pages(context)
        files.update(page_files)
        
        # Extract and generate reusable components
        components = self._extract_components(context)
        for comp_info in components:
            component_files = await self._generate_component_files(comp_info, context)
            files.update(component_files)
            
        # Generate templates for dynamic pages
        template_files = await self._generate_templates(context)
        files.update(template_files)
        
        # Generate GraphQL fragments and queries
        if self._needs_graphql(context):
            graphql_files = self._generate_graphql_files(context)
            files.update(graphql_files)
            
        # Generate utility files and hooks
        utility_files = self._generate_utilities(context)
        files.update(utility_files)
        
        # Generate styles
        style_files = self._generate_styles(context)
        files.update(style_files)
        
        # Generate SEO component
        files["src/components/seo.js"] = self._generate_seo_component(context)
        
        # Generate 404 page
        files["src/pages/404.js"] = self._generate_404_page(context)
        
        # Generate tests if requested
        if config.generate_tests:
            test_files = await self._generate_tests(components, context)
            files.update(test_files)
            
        # Generate README
        if config.generate_readme:
            files["README.md"] = self._generate_readme(context)
            
        # Generate .gitignore
        files[".gitignore"] = self._generate_gitignore()
        
        # Generate environment files
        files[".env.example"] = self._generate_env_example()
        
        return files
    
    def _generate_package_json(self, context: ExportContext) -> str:
        """Generate package.json with Gatsby dependencies"""
        config = context.config.options
        
        package_data = {
            "name": context.project.name.lower().replace(" ", "-"),
            "version": "1.0.0",
            "description": "Gatsby site exported from Canvas Editor",
            "private": True,
            "scripts": {
                "develop": "gatsby develop",
                "start": "gatsby develop",
                "build": "gatsby build",
                "serve": "gatsby serve",
                "clean": "gatsby clean",
                "test": "jest",
                "test:watch": "jest --watch",
                "type-check": "tsc --noEmit",
                "lint": "eslint src --ext .js,.jsx,.ts,.tsx",
                "format": "prettier --write \"src/**/*.{js,jsx,ts,tsx,json,md}\""
            },
            "dependencies": {
                "gatsby": "^5.12.0",
                "react": "^18.2.0",
                "react-dom": "^18.2.0"
            },
            "devDependencies": {
                "prettier": "^3.0.0"
            }
        }
        
        # Add TypeScript support
        if config.use_typescript:
            package_data["devDependencies"].update({
                "typescript": "^5.0.0",
                "@types/react": "^18.2.0",
                "@types/react-dom": "^18.2.0",
                "@types/node": "^20.0.0"
            })
        
        # Add styling dependencies
        if config.css_framework == "styled-components":
            package_data["dependencies"].update({
                "styled-components": "^6.0.0",
                "gatsby-plugin-styled-components": "^6.12.0"
            })
        elif config.css_framework == "emotion":
            package_data["dependencies"].update({
                "@emotion/react": "^11.11.0",
                "@emotion/styled": "^11.11.0",
                "gatsby-plugin-emotion": "^8.12.0"
            })
        elif config.css_framework == "sass":
            package_data["devDependencies"]["sass"] = "^1.63.0"
            package_data["dependencies"]["gatsby-plugin-sass"] = "^6.12.0"
        
        # Add image processing
        package_data["dependencies"].update({
            "gatsby-plugin-image": "^3.12.0",
            "gatsby-plugin-sharp": "^5.12.0",
            "gatsby-transformer-sharp": "^5.12.0"
        })
        
        # Add SEO and manifest
        package_data["dependencies"].update({
            "gatsby-plugin-react-helmet": "^6.12.0",
            "react-helmet": "^6.1.0",
            "gatsby-plugin-manifest": "^5.12.0"
        })
        
        # Add content management
        if config.cms == "contentful":
            package_data["dependencies"]["gatsby-source-contentful"] = "^8.12.0"
        elif config.cms == "markdown":
            package_data["dependencies"].update({
                "gatsby-source-filesystem": "^5.12.0",
                "gatsby-transformer-remark": "^6.12.0"
            })
        
        # Add testing dependencies
        if config.generate_tests:
            package_data["devDependencies"].update({
                "jest": "^29.5.0",
                "jest-environment-jsdom": "^29.5.0",
                "@testing-library/react": "^14.0.0",
                "@testing-library/jest-dom": "^5.16.0",
                "@testing-library/user-event": "^14.4.0"
            })
        
        # Add linting
        package_data["devDependencies"].update({
            "eslint": "^8.43.0",
            "eslint-plugin-react": "^7.32.0",
            "eslint-plugin-react-hooks": "^4.6.0"
        })
        
        return json.dumps(package_data, indent=2)
    
    def _generate_gatsby_config(self, context: ExportContext) -> str:
        """Generate gatsby-config.js"""
        config = context.config.options
        
        plugins = [
            "gatsby-plugin-react-helmet",
            "gatsby-plugin-image",
            "gatsby-plugin-sharp",
            "gatsby-transformer-sharp"
        ]
        
        # Add styling plugins
        if config.css_framework == "styled-components":
            plugins.append("gatsby-plugin-styled-components")
        elif config.css_framework == "emotion":
            plugins.append("gatsby-plugin-emotion")
        elif config.css_framework == "sass":
            plugins.append("gatsby-plugin-sass")
        
        # Add CMS plugins
        if config.cms == "contentful":
            plugins.append({
                "resolve": "gatsby-source-contentful",
                "options": {
                    "spaceId": "process.env.CONTENTFUL_SPACE_ID",
                    "accessToken": "process.env.CONTENTFUL_ACCESS_TOKEN"
                }
            })
        elif config.cms == "markdown":
            plugins.extend([
                {
                    "resolve": "gatsby-source-filesystem",
                    "options": {
                        "name": "content",
                        "path": f"{context.project.name}/src/content"
                    }
                },
                "gatsby-transformer-remark"
            ])
        
        # Add manifest plugin
        plugins.append({
            "resolve": "gatsby-plugin-manifest",
            "options": {
                "name": f"{context.project.name}",
                "short_name": f"{context.project.name[:12]}",
                "start_url": "/",
                "background_color": "#ffffff",
                "theme_color": "#663399",
                "display": "minimal-ui",
                "icon": "src/images/gatsby-icon.png"
            }
        })
        
        plugins_str = json.dumps(plugins, indent=4).replace('"process.env.', 'process.env.')
        
        return f"""/**
 * @type {{import('gatsby').GatsbyConfig}}
 */
module.exports = {{
  siteMetadata: {{
    title: `{context.project.name}`,
    description: `{context.project.description or 'A Gatsby site generated by Canvas Editor'}`,
    author: `Canvas Editor`,
    siteUrl: `https://example.com`,
  }},
  plugins: {plugins_str},
}};
"""
    
    def _generate_gatsby_node(self, context: ExportContext) -> str:
        """Generate gatsby-node.js for programmatic page creation"""
        ext = "tsx" if context.config.options.use_typescript else "jsx"
        
        return f"""/**
 * Implement Gatsby's Node APIs in this file.
 */

const path = require('path');

exports.createPages = async ({{ graphql, actions, reporter }}) => {{
  const {{ createPage }} = actions;

  // Define page template
  const pageTemplate = path.resolve(`src/templates/page.{ext}`);
  const blogTemplate = path.resolve(`src/templates/blog-post.{ext}`);

  // Query for markdown pages
  const result = await graphql(`
    {{
      allMarkdownRemark(
        sort: {{ frontmatter: {{ date: DESC }} }}
        limit: 1000
      ) {{
        nodes {{
          id
          frontmatter {{
            slug
            template
            title
          }}
        }}
      }}
    }}
  `);

  if (result.errors) {{
    reporter.panicOnBuild(
      `There was an error loading your content`,
      result.errors
    );
    return;
  }}

  const pages = result.data.allMarkdownRemark.nodes;

  // Create pages for each markdown file
  pages.forEach((page) => {{
    const {{ slug, template }} = page.frontmatter;
    const templatePath = template === 'blog' ? blogTemplate : pageTemplate;
    
    createPage({{
      path: slug,
      component: templatePath,
      context: {{
        id: page.id,
      }},
    }});
  }});
}};

exports.onCreateNode = ({{ node, actions, getNode }}) => {{
  const {{ createNodeField }} = actions;

  if (node.internal.type === `MarkdownRemark`) {{
    const value = node.frontmatter.slug || `/page/${{node.id}}`;
    createNodeField({{
      name: `slug`,
      node,
      value,
    }});
  }}
}};

exports.createSchemaCustomization = ({{ actions }}) => {{
  const {{ createTypes }} = actions;

  createTypes(`
    type SiteSiteMetadata {{
      author: String
      siteUrl: String
      social: Social
    }}

    type Social {{
      twitter: String
    }}

    type MarkdownRemark implements Node {{
      frontmatter: Frontmatter
      fields: Fields
    }}

    type Frontmatter {{
      title: String
      description: String
      date: Date @dateformat
      slug: String
      template: String
    }}

    type Fields {{
      slug: String
    }}
  `);
}};

// TypeScript support
{("exports.onCreateWebpackConfig = ({ actions }) => {" + """
  actions.setWebpackConfig({
    resolve: {
      extensions: ['.ts', '.tsx', '.js', '.jsx'],
    },
  });
};""" if context.config.options.use_typescript else "")}
"""
    
    def _generate_gatsby_browser(self, context: ExportContext) -> str:
        """Generate gatsby-browser.js"""
        return """/**
 * Implement Gatsby's Browser APIs in this file.
 */

// Global styles
import "./src/styles/global.css";

// Highlight.js for code syntax highlighting
// import "prismjs/themes/prism.css";

export const onClientEntry = () => {
  // IntersectionObserver polyfill for gatsby-image (Safari, IE)
  if (!(`IntersectionObserver` in window)) {
    import(`intersection-observer`);
    console.log(`# IntersectionObserver is polyfilled!`);
  }
};

export const onServiceWorkerUpdateReady = () => {
  const answer = window.confirm(
    `This application has been updated. ` +
      `Reload to display the latest version?`
  );

  if (answer === true) {
    window.location.reload();
  }
};

// Scroll restoration
export const shouldUpdateScroll = ({
  routerProps: { location },
  getSavedScrollPosition,
}) => {
  const { pathname } = location;
  
  // List of routes for the scroll restoration
  const scrollToTopRoutes = [`/`, `/about`];
  
  if (scrollToTopRoutes.includes(pathname)) {
    window.scrollTo(0, 0);
  }

  return false;
};

// Page transition hooks
export const onPreRouteUpdate = ({ location, prevLocation }) => {
  console.log("Navigating from", prevLocation?.pathname, "to", location.pathname);
};

export const onRouteUpdate = ({ location, prevLocation }) => {
  console.log("Navigated from", prevLocation?.pathname, "to", location.pathname);
};
"""
    
    def _generate_gatsby_ssr(self, context: ExportContext) -> str:
        """Generate gatsby-ssr.js"""
        return """/**
 * Implement Gatsby's SSR (Server Side Rendering) APIs in this file.
 */

const React = require("react");

exports.onRenderBody = ({
  setHtmlAttributes,
  setHeadComponents,
  setPostBodyComponents,
}) => {
  // Set HTML attributes
  setHtmlAttributes({ lang: "en" });

  // Add custom head components
  setHeadComponents([
    React.createElement("link", {
      key: "preconnect-google-fonts",
      rel: "preconnect",
      href: "https://fonts.googleapis.com",
    }),
    React.createElement("link", {
      key: "preconnect-google-fonts-gstatic",
      rel: "preconnect",
      href: "https://fonts.gstatic.com",
      crossOrigin: "anonymous",
    }),
    React.createElement("link", {
      key: "google-fonts",
      rel: "stylesheet",
      href: "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap",
    }),
  ]);
};

exports.onPreRenderHTML = ({
  getHeadComponents,
  replaceHeadComponents,
}) => {
  const headComponents = getHeadComponents();

  // Reorder head components for better performance
  headComponents.sort((x, y) => {
    if (x.props && x.props.rel === 'stylesheet') {
      return -1;
    } else if (y.props && y.props.rel === 'stylesheet') {
      return 1;
    }
    return 0;
  });

  replaceHeadComponents(headComponents);
};
"""
    
    async def _generate_layouts(self, context: ExportContext) -> Dict[str, str]:
        """Generate layout components"""
        files = {}
        config = context.config.options
        ext = "tsx" if config.use_typescript else "jsx"
        
        # Main layout component
        files[f"src/components/layout.{ext}"] = await self._generate_main_layout(context)
        
        # Header component
        files[f"src/components/header.{ext}"] = self._generate_header_component(context)
        
        # Footer component
        files[f"src/components/footer.{ext}"] = self._generate_footer_component(context)
        
        return files
    
    async def _generate_main_layout(self, context: ExportContext) -> str:
        """Generate main layout component"""
        config = context.config.options
        
        imports = ["import React from 'react';"]
        
        if config.use_typescript:
            imports.append("import { ReactNode } from 'react';")
        
        imports.extend([
            "import Header from './header';",
            "import Footer from './footer';",
            "import './layout.css';"
        ])
        
        children_type = ": { children: ReactNode }" if config.use_typescript else ""
        
        return f"""{chr(10).join(imports)}

const Layout = ({{ children }}{children_type}) => {{
  return (
    <div className="layout">
      <Header />
      <main className="main-content">
        {children}
      </main>
      <Footer />
    </div>
  );
}};

export default Layout;
"""
    
    def _generate_header_component(self, context: ExportContext) -> str:
        """Generate header component"""
        config = context.config.options
        
        imports = ["import React from 'react';"]
        if config.use_gatsby_link:
            imports.append("import { Link } from 'gatsby';")
        
        link_component = "Link" if config.use_gatsby_link else "a"
        to_prop = "to" if config.use_gatsby_link else "href"
        
        return f"""{chr(10).join(imports)}

const Header = () => {{
  return (
    <header className="header">
      <div className="container">
        <div className="header-content">
          <{link_component} {to_prop}="/" className="site-title">
            {context.project.name}
          </{link_component}>
          
          <nav className="navigation">
            <ul className="nav-list">
              <li>
                <{link_component} {to_prop}="/" className="nav-link">
                  Home
                </{link_component}>
              </li>
              <li>
                <{link_component} {to_prop}="/about" className="nav-link">
                  About
                </{link_component}>
              </li>
              <li>
                <{link_component} {to_prop}="/contact" className="nav-link">
                  Contact
                </{link_component}>
              </li>
            </ul>
          </nav>
        </div>
      </div>
    </header>
  );
}};

export default Header;
"""
    
    def _generate_footer_component(self, context: ExportContext) -> str:
        """Generate footer component"""
        return f"""import React from 'react';

const Footer = () => {{
  return (
    <footer className="footer">
      <div className="container">
        <div className="footer-content">
          <p>&copy; {{new Date().getFullYear()}} {context.project.name}. All rights reserved.</p>
          <p>Built with Gatsby and exported from Canvas Editor.</p>
        </div>
      </div>
    </footer>
  );
}};

export default Footer;
"""
    
    async def _generate_pages(self, context: ExportContext) -> Dict[str, str]:
        """Generate page components"""
        files = {}
        config = context.config.options
        ext = "tsx" if config.use_typescript else "jsx"
        
        # Index page
        files[f"src/pages/index.{ext}"] = await self._generate_index_page(context)
        
        # About page
        files[f"src/pages/about.{ext}"] = self._generate_about_page(context)
        
        # Contact page
        files[f"src/pages/contact.{ext}"] = self._generate_contact_page(context)
        
        return files
    
    async def _generate_index_page(self, context: ExportContext) -> str:
        """Generate index page"""
        config = context.config.options
        
        # Convert root components to Gatsby JSX
        root_components = self._get_root_components(context)
        jsx_content = await self._components_to_jsx(root_components, context, 4)
        
        graphql_query = ""
        if self._needs_graphql(context):
            graphql_query = """
export const query = graphql`
  query {
    site {
      siteMetadata {
        title
        description
      }
    }
  }
`;"""
        
        data_prop = ""
        page_data = ""
        if self._needs_graphql(context):
            data_prop = ", { data }" if config.use_typescript else ", { data }"
            page_data = """
  const { title, description } = data.site.siteMetadata;
"""
        
        imports = [
            "import React from 'react';",
            "import Layout from '../components/layout';",
            "import Seo from '../components/seo';"
        ]
        
        if self._needs_graphql(context):
            imports.append("import { graphql } from 'gatsby';")
        
        page_props = ": { data?: any }" if config.use_typescript else ""
        
        return f"""{chr(10).join(imports)}

const IndexPage = ({{ location }}{data_prop}){page_props} => {{{page_data}
  return (
    <Layout>
      <Seo title="Home" />
      <div className="page-content">
        <section className="hero">
          <div className="container">
            <h1 className="hero-title">{context.project.name}</h1>
            <p className="hero-description">
              {context.project.description or 'Welcome to our Gatsby site!'}
            </p>
          </div>
        </section>
        
        <section className="content">
          <div className="container">
{jsx_content}
          </div>
        </section>
      </div>
    </Layout>
  );
}};

export default IndexPage;
{graphql_query}
"""
    
    def _generate_about_page(self, context: ExportContext) -> str:
        """Generate about page"""
        config = context.config.options
        page_props = ": { location: Location }" if config.use_typescript else ""
        
        imports = ["import React from 'react';"]
        if config.use_typescript:
            imports.append("import { Location } from '@reach/router';")
        imports.extend([
            "import Layout from '../components/layout';",
            "import Seo from '../components/seo';"
        ])
        
        return f"""{chr(10).join(imports)}

const AboutPage = ({{ location }}){page_props} => {{
  return (
    <Layout>
      <Seo title="About" />
      <div className="page-content">
        <div className="container">
          <h1>About Us</h1>
          <p>
            This is an about page for {context.project.name}. 
            Generated by Canvas Editor using Gatsby.
          </p>
          <p>
            Gatsby is a modern framework for building fast websites 
            with React and GraphQL.
          </p>
        </div>
      </div>
    </Layout>
  );
}};

export default AboutPage;
"""
    
    def _generate_contact_page(self, context: ExportContext) -> str:
        """Generate contact page"""
        config = context.config.options
        page_props = ": { location: Location }" if config.use_typescript else ""
        
        imports = ["import React from 'react';"]
        if config.use_typescript:
            imports.append("import { Location } from '@reach/router';")
        imports.extend([
            "import Layout from '../components/layout';",
            "import Seo from '../components/seo';"
        ])
        
        return f"""{chr(10).join(imports)}

const ContactPage = ({{ location }}){page_props} => {{
  return (
    <Layout>
      <Seo title="Contact" />
      <div className="page-content">
        <div className="container">
          <h1>Contact Us</h1>
          <p>Get in touch with us using the form below.</p>
          
          <form className="contact-form" netlify>
            <div className="form-group">
              <label htmlFor="name">Name:</label>
              <input type="text" id="name" name="name" required />
            </div>
            
            <div className="form-group">
              <label htmlFor="email">Email:</label>
              <input type="email" id="email" name="email" required />
            </div>
            
            <div className="form-group">
              <label htmlFor="message">Message:</label>
              <textarea id="message" name="message" rows={{5}} required></textarea>
            </div>
            
            <button type="submit" className="submit-button">
              Send Message
            </button>
          </form>
        </div>
      </div>
    </Layout>
  );
}};

export default ContactPage;
"""
    
    def _generate_seo_component(self, context: ExportContext) -> str:
        """Generate SEO component"""
        config = context.config.options
        
        imports = ["import React from 'react';"]
        imports.append("import { Helmet } from 'react-helmet';")
        imports.append("import { useStaticQuery, graphql } from 'gatsby';")
        
        seo_props = ""
        if config.use_typescript:
            seo_props = """: {
  title?: string;
  description?: string;
  meta?: Array<{ name: string; content: string }>;
  lang?: string;
}"""
        
        return f"""{chr(10).join(imports)}

const Seo = ({{
  title,
  description,
  meta = [],
  lang = 'en'
}}){seo_props} => {{
  const {{ site }} = useStaticQuery(
    graphql`
      query {{
        site {{
          siteMetadata {{
            title
            description
            author
          }}
        }}
      }}
    `
  );

  const metaDescription = description || site.siteMetadata.description;
  const defaultTitle = site.siteMetadata?.title;

  return (
    <Helmet
      htmlAttributes={{{{ lang }}}}
      title={{title}}
      titleTemplate={{defaultTitle ? `%s | ${{defaultTitle}}` : undefined}}
      meta={{[
        {{
          name: 'description',
          content: metaDescription,
        }},
        {{
          property: 'og:title',
          content: title,
        }},
        {{
          property: 'og:description',
          content: metaDescription,
        }},
        {{
          property: 'og:type',
          content: 'website',
        }},
        {{
          name: 'twitter:card',
          content: 'summary',
        }},
        {{
          name: 'twitter:creator',
          content: site.siteMetadata?.author || '',
        }},
        {{
          name: 'twitter:title',
          content: title,
        }},
        {{
          name: 'twitter:description',
          content: metaDescription,
        }},
      ].concat(meta)}}
    />
  );
}};

export default Seo;
"""
    
    def _generate_404_page(self, context: ExportContext) -> str:
        """Generate 404 page"""
        config = context.config.options
        page_props = ": { location: Location }" if config.use_typescript else ""
        
        imports = ["import React from 'react';"]
        if config.use_typescript:
            imports.append("import { Location } from '@reach/router';")
        imports.extend([
            "import Layout from '../components/layout';",
            "import Seo from '../components/seo';"
        ])
        
        return f"""{chr(10).join(imports)}

const NotFoundPage = ({{ location }}){page_props} => {{
  return (
    <Layout>
      <Seo title="404: Not found" />
      <div className="page-content">
        <div className="container">
          <div className="not-found">
            <h1>404: Not Found</h1>
            <p>You just hit a route that doesn't exist... the sadness.</p>
            <p>
              <a href="/">Go back to the homepage</a>
            </p>
          </div>
        </div>
      </div>
    </Layout>
  );
}};

export default NotFoundPage;
"""
    
    async def _generate_templates(self, context: ExportContext) -> Dict[str, str]:
        """Generate template files for dynamic pages"""
        files = {}
        config = context.config.options
        ext = "tsx" if config.use_typescript else "jsx"
        
        # Page template
        files[f"src/templates/page.{ext}"] = self._generate_page_template(context)
        
        # Blog post template
        files[f"src/templates/blog-post.{ext}"] = self._generate_blog_template(context)
        
        return files
    
    def _generate_page_template(self, context: ExportContext) -> str:
        """Generate page template"""
        config = context.config.options
        
        imports = [
            "import React from 'react';",
            "import { graphql } from 'gatsby';",
            "import Layout from '../components/layout';",
            "import Seo from '../components/seo';"
        ]
        
        template_props = ""
        if config.use_typescript:
            template_props = ": { data: any; location: Location }"
            imports.append("import { Location } from '@reach/router';")
        
        return f"""{chr(10).join(imports)}

const PageTemplate = ({{ data, location }}){template_props} => {{
  const page = data.markdownRemark;

  return (
    <Layout>
      <Seo
        title={{page.frontmatter.title}}
        description={{page.frontmatter.description || page.excerpt}}
      />
      <article className="page">
        <div className="container">
          <header className="page-header">
            <h1>{{page.frontmatter.title}}</h1>
            {{page.frontmatter.description && (
              <p className="page-description">{{page.frontmatter.description}}</p>
            )}}
          </header>
          <div
            className="page-content"
            dangerouslySetInnerHTML={{{{ __html: page.html }}}}
          />
        </div>
      </article>
    </Layout>
  );
}};

export default PageTemplate;

export const pageQuery = graphql`
  query PageBySlug($id: String!) {{
    site {{
      siteMetadata {{
        title
      }}
    }}
    markdownRemark(id: {{ eq: $id }}) {{
      id
      excerpt(pruneLength: 160)
      html
      frontmatter {{
        title
        description
        date(formatString: "MMMM DD, YYYY")
      }}
    }}
  }}
`;
"""
    
    def _generate_blog_template(self, context: ExportContext) -> str:
        """Generate blog post template"""
        config = context.config.options
        
        imports = [
            "import React from 'react';",
            "import { Link, graphql } from 'gatsby';",
            "import Layout from '../components/layout';",
            "import Seo from '../components/seo';"
        ]
        
        template_props = ""
        if config.use_typescript:
            template_props = ": { data: any; location: Location }"
            imports.append("import { Location } from '@reach/router';")
        
        return f"""{chr(10).join(imports)}

const BlogPostTemplate = ({{ data, location }}){template_props} => {{
  const post = data.markdownRemark;
  const siteTitle = data.site.siteMetadata?.title || 'Title';
  const {{ previous, next }} = data;

  return (
    <Layout>
      <Seo
        title={{post.frontmatter.title}}
        description={{post.frontmatter.description || post.excerpt}}
      />
      <article className="blog-post" itemScope itemType="http://schema.org/Article">
        <div className="container">
          <header className="blog-post-header">
            <h1 itemProp="headline">{{post.frontmatter.title}}</h1>
            <p className="blog-post-meta">{{post.frontmatter.date}}</p>
          </header>
          <section
            dangerouslySetInnerHTML={{{{ __html: post.html }}}}
            itemProp="articleBody"
            className="blog-post-content"
          />
          <hr />
          <footer className="blog-post-footer">
            <p>
              Written by <strong itemProp="author">{{post.frontmatter.author || 'Canvas Editor'}}</strong>
            </p>
          </footer>
        </div>
      </article>
      
      <nav className="blog-post-nav">
        <div className="container">
          <ul className="nav-list">
            <li>
              {{previous && (
                <Link to={{previous.fields.slug}} rel="prev">
                  ← {{previous.frontmatter.title}}
                </Link>
              )}}
            </li>
            <li>
              {{next && (
                <Link to={{next.fields.slug}} rel="next">
                  {{next.frontmatter.title}} →
                </Link>
              )}}
            </li>
          </ul>
        </div>
      </nav>
    </Layout>
  );
}};

export default BlogPostTemplate;

export const pageQuery = graphql`
  query BlogPostBySlug(
    $id: String!
    $previousPostId: String
    $nextPostId: String
  ) {{
    site {{
      siteMetadata {{
        title
      }}
    }}
    markdownRemark(id: {{ eq: $id }}) {{
      id
      excerpt(pruneLength: 160)
      html
      frontmatter {{
        title
        date(formatString: "MMMM DD, YYYY")
        description
        author
      }}
    }}
    previous: markdownRemark(id: {{ eq: $previousPostId }}) {{
      fields {{
        slug
      }}
      frontmatter {{
        title
      }}
    }}
    next: markdownRemark(id: {{ eq: $nextPostId }}) {{
      fields {{
        slug
      }}
      frontmatter {{
        title
      }}
    }}
  }}
`;
"""
    
    async def _generate_component_files(self, comp_info, context: ExportContext) -> Dict[str, str]:
        """Generate component files"""
        files = {}
        config = context.config.options
        ext = "tsx" if config.use_typescript else "jsx"
        
        # Component file
        files[f"src/components/{self._to_kebab_case(comp_info['name'])}.{ext}"] = await self._generate_component_jsx(comp_info, context)
        
        # Component test
        if config.generate_tests:
            files[f"src/components/{self._to_kebab_case(comp_info['name'])}.test.{ext}"] = self._generate_component_test(comp_info)
        
        return files
    
    async def _generate_component_jsx(self, comp_info, context: ExportContext) -> str:
        """Generate component JSX"""
        config = context.config.options
        
        imports = ["import React from 'react';"]
        
        # Generate props interface for TypeScript
        props_interface = ""
        if config.use_typescript and comp_info.get('props'):
            prop_types = []
            for prop in comp_info['props']:
                optional = "?" if prop.get("optional", True) else ""
                prop_types.append(f"  {prop['name']}{optional}: {prop['type']};")
            
            props_interface = f"""
interface {comp_info['name']}Props {{
{chr(10).join(prop_types)}
}}

"""
        
        # Generate component
        jsx_content = await self._component_to_jsx(comp_info['component'], context, 1)
        
        props_destructure = ""
        if comp_info.get('props'):
            prop_names = [prop['name'] for prop in comp_info['props']]
            props_destructure = f"{{ {', '.join(prop_names)} }}"
        
        props_type = f": {comp_info['name']}Props" if config.use_typescript and comp_info.get('props') else ""
        
        return f"""{chr(10).join(imports)}

{props_interface}const {comp_info['name']} = ({props_destructure}){props_type} => {{
  return (
{jsx_content}
  );
}};

export default {comp_info['name']};
"""
    
    async def _components_to_jsx(self, components: List[Component], context: ExportContext, indent: int = 0) -> str:
        """Convert components to Gatsby JSX"""
        jsx_parts = []
        
        for component in components:
            jsx = await self._component_to_jsx(component, context, indent)
            jsx_parts.append(jsx)
            
        return "\n".join(jsx_parts)
    
    async def _component_to_jsx(self, component: Component, context: ExportContext, indent: int = 0) -> str:
        """
        Convert single component to Gatsby JSX
        
        CLAUDE.md #7.2: Escape user content
        """
        indent_str = "  " * indent
        
        # Handle text nodes
        if component.type == "text":
            content = self._escape_jsx_text(component.content)
            return f"{indent_str}{content}"
        
        # Map to Gatsby element or component
        element = self._map_to_gatsby_element(component.type)
        
        # Build props
        props = self._build_jsx_props(component)
        
        # Handle self-closing elements
        if not component.children and not component.content:
            return f"{indent_str}<{element}{props} />"
        
        # Handle elements with children
        jsx_lines = [f"{indent_str}<{element}{props}>"]
        
        # Add content
        if component.content:
            escaped_content = self._escape_jsx_text(component.content)
            jsx_lines.append(f"{indent_str}  {escaped_content}")
        
        # Add children
        for child in component.children:
            child_jsx = await self._component_to_jsx(child, context, indent + 1)
            jsx_lines.append(child_jsx)
        
        jsx_lines.append(f"{indent_str}</{element}>")
        
        return "\n".join(jsx_lines)
    
    def _map_to_gatsby_element(self, component_type: str) -> str:
        """Map component type to Gatsby element or component"""
        # Map to HTML elements or Gatsby components
        element_map = {
            "container": "div",
            "text": "span",
            "heading": "h2",
            "paragraph": "p",
            "link": "Link",  # Gatsby Link component
            "button": "button",
            "image": "GatsbyImage",  # Gatsby Image component
            "list": "ul",
            "listitem": "li",
            "form": "form",
            "input": "input",
            "textarea": "textarea",
            "select": "select"
        }
        
        return element_map.get(component_type, "div")
    
    def _build_jsx_props(self, component: Component) -> str:
        """Build JSX props string for Gatsby"""
        props = {}
        
        # Class name
        if component.class_name:
            props["className"] = component.class_name
        
        # Style
        if component.styles:
            style_obj = self._styles_to_jsx_object(component.styles)
            if style_obj:
                props["style"] = style_obj
        
        # Event handlers
        if hasattr(component, "events"):
            for event, handler in component.events.items():
                react_event = self._map_event_name(event)
                props[react_event] = f"{{{handler}}}"
        
        # Component-specific props
        if component.type == "link":
            props["to"] = component.properties.get("href", "/")
            if component.properties.get("target") == "_blank":
                props["target"] = "_blank"
                props["rel"] = "noopener noreferrer"
        
        elif component.type == "image":
            props["src"] = component.properties.get("src", "")
            props["alt"] = component.properties.get("alt", "")
        
        elif component.type == "input":
            props["type"] = component.properties.get("type", "text")
            props["name"] = component.properties.get("name", "")
            
            if component.properties.get("placeholder"):
                props["placeholder"] = component.properties["placeholder"]
            if component.properties.get("required"):
                props["required"] = True
        
        # Build props string
        if not props:
            return ""
        
        prop_strings = []
        for key, value in props.items():
            if isinstance(value, bool):
                if value:
                    prop_strings.append(key)
            elif isinstance(value, str):
                if value.startswith("{") and value.endswith("}"):
                    prop_strings.append(f"{key}={value}")
                else:
                    prop_strings.append(f'{key}="{self._escape_jsx_attribute(value)}"')
            else:
                prop_strings.append(f"{key}={{{json.dumps(value)}}}")
        
        return " " + " ".join(prop_strings) if prop_strings else ""
    
    def _escape_jsx_text(self, text: str) -> str:
        """
        Escape text for JSX
        
        CLAUDE.md #7.2: Prevent XSS
        """
        if not text:
            return ""
        
        text = str(text)
        text = text.replace("{", "&#123;")
        text = text.replace("}", "&#125;")
        text = text.replace("<", "&lt;")
        text = text.replace(">", "&gt;")
        
        return text
    
    def _escape_jsx_attribute(self, value: str) -> str:
        """Escape attribute value for JSX"""
        value = value.replace('"', '&quot;')
        value = value.replace("'", '&#39;')
        return value
    
    def _generate_styles(self, context: ExportContext) -> Dict[str, str]:
        """Generate style files"""
        files = {}
        
        # Global styles
        files["src/styles/global.css"] = self._generate_global_css(context)
        
        # Layout styles
        files["src/components/layout.css"] = self._generate_layout_css(context)
        
        return files
    
    def _generate_global_css(self, context: ExportContext) -> str:
        """Generate global CSS"""
        return """/* Global styles */
*, *::before, *::after {
  box-sizing: border-box;
}

html {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  -ms-text-size-adjust: 100%;
  -webkit-text-size-adjust: 100%;
}

body {
  margin: 0;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #333;
  background-color: #fff;
  line-height: 1.6;
}

/* Typography */
h1, h2, h3, h4, h5, h6 {
  margin: 0 0 1rem 0;
  font-weight: 600;
  line-height: 1.25;
}

h1 { font-size: 2.5rem; }
h2 { font-size: 2rem; }
h3 { font-size: 1.75rem; }
h4 { font-size: 1.5rem; }
h5 { font-size: 1.25rem; }
h6 { font-size: 1rem; }

p {
  margin: 0 0 1rem 0;
}

a {
  color: #663399;
  text-decoration: none;
}

a:hover {
  text-decoration: underline;
}

/* Utilities */
.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1rem;
}

@media (min-width: 768px) {
  .container {
    padding: 0 2rem;
  }
}

/* Accessibility */
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

/* Focus styles */
a:focus,
button:focus,
input:focus,
textarea:focus,
select:focus {
  outline: 2px solid #663399;
  outline-offset: 2px;
}

/* Forms */
.form-group {
  margin-bottom: 1rem;
}

label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
}

input,
textarea,
select {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
}

button {
  background: #663399;
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
  transition: background-color 0.2s;
}

button:hover {
  background: #552288;
}

/* Page content */
.page-content {
  min-height: 60vh;
  padding: 2rem 0;
}

/* Hero section */
.hero {
  background: linear-gradient(135deg, #663399 0%, #552288 100%);
  color: white;
  padding: 4rem 0;
  text-align: center;
}

.hero-title {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.hero-description {
  font-size: 1.25rem;
  opacity: 0.9;
}

@media (max-width: 768px) {
  .hero-title {
    font-size: 2rem;
  }
  
  .hero-description {
    font-size: 1rem;
  }
}

/* Blog styles */
.blog-post-header {
  margin-bottom: 2rem;
  text-align: center;
  border-bottom: 1px solid #eee;
  padding-bottom: 2rem;
}

.blog-post-meta {
  color: #666;
  font-size: 0.9rem;
}

.blog-post-content {
  max-width: 800px;
  margin: 0 auto;
  line-height: 1.8;
}

.blog-post-content img {
  max-width: 100%;
  height: auto;
  border-radius: 8px;
  margin: 2rem 0;
}

.blog-post-nav {
  margin-top: 3rem;
  padding-top: 2rem;
  border-top: 1px solid #eee;
}

.blog-post-nav .nav-list {
  display: flex;
  justify-content: space-between;
  list-style: none;
  padding: 0;
  margin: 0;
}

.blog-post-nav .nav-list li {
  flex: 1;
}

.blog-post-nav .nav-list li:last-child {
  text-align: right;
}

/* Contact form */
.contact-form {
  max-width: 600px;
  margin: 2rem auto;
}

.submit-button {
  background: #663399;
  color: white;
  border: none;
  padding: 1rem 2rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
  transition: background-color 0.2s;
}

.submit-button:hover {
  background: #552288;
}

/* 404 page */
.not-found {
  text-align: center;
  padding: 4rem 0;
}

.not-found h1 {
  font-size: 4rem;
  color: #663399;
  margin-bottom: 1rem;
}
"""
    
    def _generate_layout_css(self, context: ExportContext) -> str:
        """Generate layout CSS"""
        return """.layout {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.main-content {
  flex: 1;
}

/* Header */
.header {
  background: white;
  border-bottom: 1px solid #eee;
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 0;
}

.site-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: #663399;
  text-decoration: none;
}

.site-title:hover {
  text-decoration: none;
}

.navigation .nav-list {
  display: flex;
  list-style: none;
  margin: 0;
  padding: 0;
  gap: 2rem;
}

.nav-link {
  color: #333;
  text-decoration: none;
  font-weight: 500;
  transition: color 0.2s;
}

.nav-link:hover {
  color: #663399;
  text-decoration: none;
}

/* Footer */
.footer {
  background: #f8f9fa;
  border-top: 1px solid #eee;
  padding: 2rem 0;
  margin-top: auto;
}

.footer-content {
  text-align: center;
  color: #666;
}

.footer-content p {
  margin: 0.5rem 0;
}

/* Responsive */
@media (max-width: 768px) {
  .header-content {
    flex-direction: column;
    gap: 1rem;
  }
  
  .navigation .nav-list {
    gap: 1rem;
  }
}
"""
    
    def _generate_utilities(self, context: ExportContext) -> Dict[str, str]:
        """Generate utility files"""
        files = {}
        config = context.config.options
        ext = "ts" if config.use_typescript else "js"
        
        # Utility functions
        files[f"src/utils/index.{ext}"] = """// Utility functions

export function formatDate(date: string | Date): string {
  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  }).format(new Date(date));
}

export function slugify(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9 -]/g, '')
    .replace(/\\s+/g, '-')
    .replace(/-+/g, '-')
    .trim('-');
}

export function truncate(text: string, length: number = 100): string {
  if (text.length <= length) return text;
  return text.substring(0, length).trim() + '...';
}

export function classNames(...classes: (string | undefined | null | false)[]): string {
  return classes.filter(Boolean).join(' ');
}
"""
        
        return files
    
    def _generate_tsconfig(self) -> str:
        """Generate TypeScript configuration"""
        return """{
  "compilerOptions": {
    "target": "esnext",
    "lib": ["dom", "dom.iterable", "es6"],
    "allowJs": true,
    "skipLibCheck": true,
    "esModuleInterop": true,
    "allowSyntheticDefaultImports": true,
    "strict": true,
    "forceConsistentCasingInFileNames": true,
    "module": "esnext",
    "moduleResolution": "node",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"]
    }
  },
  "include": [
    "src/**/*",
    "gatsby-config.js",
    "gatsby-node.js",
    "gatsby-browser.js",
    "gatsby-ssr.js"
  ],
  "exclude": [
    "node_modules",
    "public",
    ".cache"
  ]
}
"""
    
    def _generate_readme(self, context: ExportContext) -> str:
        """Generate README.md"""
        return f"""# {context.project.name}

A Gatsby site exported from Canvas Editor.

## 🚀 Quick start

1. **Start developing.**

   Navigate into your new site's directory and start it up.

   ```shell
   cd {context.project.name.lower().replace(" ", "-")}
   gatsby develop
   ```

2. **Open the source code and start editing!**

   Your site is now running at `http://localhost:8000`!

   _Note: You'll also see a second link: `http://localhost:8000/___graphql`. This is a tool you can use to experiment with querying your data. Learn more about using this tool in the [Gatsby tutorial](https://www.gatsbyjs.com/tutorial/part-five/#introducing-graphiql)._

   Open the `{context.project.name.lower().replace(" ", "-")}` directory in your code editor of choice and edit `src/pages/index.js`. Save your changes and the browser will update in real time!

## 🧐 What's inside?

A quick look at the top-level files and directories you'll see in a Gatsby project.

    .
    ├── node_modules
    ├── src
    ├── .gitignore
    ├── .prettierrc
    ├── gatsby-browser.js
    ├── gatsby-config.js
    ├── gatsby-node.js
    ├── gatsby-ssr.js
    ├── LICENSE
    ├── package-lock.json
    ├── package.json
    └── README.md

1. **`/node_modules`**: This directory contains all of the modules of code that your project depends on (npm packages) are automatically installed.

2. **`/src`**: This directory will contain all of the code related to what you will see on the front-end of your site (what you see in the browser) such as your site header or a page template. `src` is a convention for "source code".

3. **`.gitignore`**: This file tells git which files it should not track / not maintain a version history for.

4. **`.prettierrc`**: This is a configuration file for [Prettier](https://prettier.io/). Prettier is a tool to help keep the formatting of your code consistent.

5. **`gatsby-browser.js`**: This file is where Gatsby expects to find any usage of the [Gatsby browser APIs](https://www.gatsbyjs.com/docs/browser-apis/) (if any). These allow customization/extension of default Gatsby settings affecting the browser.

6. **`gatsby-config.js`**: This is the main configuration file for a Gatsby site. This is where you can specify information about your site (metadata) like the site title and description, which Gatsby plugins you'd like to include, etc. (Check out the [config docs](https://www.gatsbyjs.com/docs/gatsby-config/) for more detail).

7. **`gatsby-node.js`**: This file is where Gatsby expects to find any usage of the [Gatsby Node APIs](https://www.gatsbyjs.com/docs/node-apis/) (if any). These allow customization/extension of default Gatsby settings affecting pieces of the site build process.

8. **`gatsby-ssr.js`**: This file is where Gatsby expects to find any usage of the [Gatsby server-side rendering APIs](https://www.gatsbyjs.com/docs/ssr-apis/) (if any). These allow customization of default Gatsby settings affecting server-side rendering.

9. **`LICENSE`**: This Gatsby starter is licensed under the 0BSD license. This means that you can see this file as a placeholder and replace it with your own license.

10. **`package-lock.json`** (See `package.json` below, first). This is an automatically generated file based on the exact versions of your npm dependencies that were installed for your project. **(You won't change this file directly).**

11. **`package.json`**: A manifest file for Node.js projects, which includes things like metadata (the project's name, author, etc). This manifest is how npm knows which packages to install for your project.

12. **`README.md`**: A text file containing useful reference information about your project.

## 🎓 Learning Gatsby

Looking for more guidance? Full documentation for Gatsby lives [on the website](https://www.gatsbyjs.com/). Here are some places to start:

- **For most developers, we recommend starting with our [in-depth tutorial for creating a site with Gatsby](https://www.gatsbyjs.com/tutorial/).** It starts with zero assumptions about your level of ability and walks through every step of the process.

- **To dive straight into code samples, head [to our documentation](https://www.gatsbyjs.com/docs/).** In particular, check out the _Guides_, _API Reference_, and _Advanced Tutorials_ sections in the sidebar.

## 💫 Deploy

[Build, Deploy, and Host On The Only Cloud Built For Gatsby](https://www.gatsbyjs.com/products/cloud/)

Gatsby Cloud is an end-to-end cloud platform specifically built for the Gatsby framework that combines a modern developer experience with an optimized, global edge network.

## 🚀 Other deployment options

You can deploy this site to various platforms:

- [Netlify](https://www.netlify.com/)
- [Vercel](https://vercel.com/)
- [GitHub Pages](https://pages.github.com/)
- [AWS S3](https://aws.amazon.com/s3/)

## 📝 Features

- ⚡️ Fast static site generation with Gatsby
- 🎨 Modern React components
- 📱 Responsive design
- 🔧 TypeScript support (optional)
- 🧪 Testing with Jest
- 📈 SEO optimized
- 🖼️ Optimized images with gatsby-plugin-image
- 🎯 PWA ready

Generated by Canvas Editor.
"""
    
    def _generate_gitignore(self) -> str:
        """Generate .gitignore"""
        return """# Logs
logs
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Runtime data
pids
*.pid
*.seed
*.pid.lock

# Coverage directory used by tools like istanbul
coverage/

# nyc test coverage
.nyc_output

# Grunt intermediate storage (https://gruntjs.com/creating-plugins#storing-task-files)
.grunt

# Bower dependency directory (https://bower.io/)
bower_components

# node-waf configuration
.lock-wscript

# Compiled binary addons (https://nodejs.org/api/addons.html)
build/Release

# Dependency directories
node_modules/
jspm_packages/

# TypeScript cache
*.tsbuildinfo

# Optional npm cache directory
.npm

# Optional eslint cache
.eslintcache

# Microbundle cache
.rpt2_cache/
.rts2_cache_cjs/
.rts2_cache_es/
.rts2_cache_umd/

# Optional REPL history
.node_repl_history

# Output of 'npm pack'
*.tgz

# Yarn Integrity file
.yarn-integrity

# dotenv environment variables file
.env
.env.development
.env.local
.env.production

# parcel-bundler cache (https://parceljs.org/)
.cache/
.parcel-cache/

# Gatsby files
.cache/
public

# Stores VSCode versions used for testing VSCode extensions
.vscode-test

# Mac files
.DS_Store

# Yarn
yarn-error.log
.pnp/
.pnp.js
# Yarn Integrity file
.yarn-integrity
"""
    
    def _generate_env_example(self) -> str:
        """Generate .env.example"""
        return """# Environment variables example

# Site URL (for SEO and social sharing)
GATSBY_SITE_URL=https://example.com

# Contentful (if using)
# CONTENTFUL_SPACE_ID=your_space_id
# CONTENTFUL_ACCESS_TOKEN=your_access_token

# Google Analytics (if using)
# GATSBY_GOOGLE_ANALYTICS_TRACKING_ID=UA-XXXXXXXXX-X

# Other APIs
# GATSBY_API_URL=https://api.example.com
"""
    
    # Helper methods
    def _needs_graphql(self, context: ExportContext) -> bool:
        """Check if GraphQL is needed"""
        return context.config.options.cms in ["contentful", "markdown"] or self._has_dynamic_content(context)
    
    def _has_dynamic_content(self, context: ExportContext) -> bool:
        """Check if project has dynamic content"""
        return any(comp.properties.get("dynamic", False) for comp in context.project.components)
    
    def _get_root_components(self, context: ExportContext) -> List[Component]:
        """Get root components"""
        return [comp for comp in context.project.components if not comp.parent_id]
    
    def _extract_components(self, context: ExportContext) -> List[Dict[str, Any]]:
        """Extract reusable components"""
        components = []
        
        # Group components by type and properties
        component_groups = {}
        for comp in context.project.components:
            signature = (comp.type, tuple(sorted(comp.properties.items())))
            if signature not in component_groups:
                component_groups[signature] = []
            component_groups[signature].append(comp)
        
        # Extract components used multiple times
        for signature, group in component_groups.items():
            if len(group) >= 2:  # Used 2+ times
                comp_info = {
                    "component": group[0],
                    "name": self._generate_component_name(group[0]),
                    "props": self._extract_props(group)
                }
                components.append(comp_info)
        
        return components
    
    def _generate_component_name(self, component: Component) -> str:
        """Generate component name (PascalCase)"""
        name = component.type.replace("_", " ").replace("-", " ")
        name = "".join(word.capitalize() for word in name.split())
        
        if not name[0].isupper():
            name = "Custom" + name
        
        return name
    
    def _to_kebab_case(self, text: str) -> str:
        """Convert to kebab-case"""
        import re
        text = re.sub('([a-z0-9])([A-Z])', r'\1-\2', text)
        return text.lower().replace('_', '-').replace(' ', '-')
    
    def _extract_props(self, component_group: List[Component]) -> List[Dict[str, str]]:
        """Extract varying properties as props"""
        props = []
        
        # Find properties that vary across instances
        all_props = {}
        for comp in component_group:
            for key, value in comp.properties.items():
                if key not in all_props:
                    all_props[key] = set()
                all_props[key].add(str(value))
        
        # Create prop info for varying properties
        for key, values in all_props.items():
            if len(values) > 1:
                props.append({
                    "name": key,
                    "type": self._infer_typescript_type(values),
                    "optional": True
                })
        
        return props
    
    def _infer_typescript_type(self, values: Set[str]) -> str:
        """Infer TypeScript type from values"""
        try:
            numbers = [float(v) for v in values]
            return "number"
        except ValueError:
            pass
        
        if all(v.lower() in ["true", "false"] for v in values):
            return "boolean"
        
        return "string"
    
    def _styles_to_jsx_object(self, styles: Dict[str, Any]) -> Dict[str, Any]:
        """Convert styles to JSX style object"""
        jsx_styles = {}
        for key, value in styles.items():
            # Convert kebab-case to camelCase
            camel_key = self._kebab_to_camel(key)
            jsx_styles[camel_key] = value
        return jsx_styles
    
    def _kebab_to_camel(self, name: str) -> str:
        """Convert kebab-case to camelCase"""
        parts = name.split("-")
        return parts[0] + "".join(part.capitalize() for part in parts[1:])
    
    def _map_event_name(self, event: str) -> str:
        """Map event name to React convention"""
        event_map = {
            "click": "onClick",
            "change": "onChange",
            "submit": "onSubmit",
            "focus": "onFocus",
            "blur": "onBlur"
        }
        return event_map.get(event, f"on{event.capitalize()}")
    
    def _generate_graphql_files(self, context: ExportContext) -> Dict[str, str]:
        """Generate GraphQL fragments and queries"""
        files = {}
        
        # Example fragments
        files["src/graphql/fragments.js"] = """import { graphql } from 'gatsby';

export const siteMetadata = graphql`
  fragment SiteMetadata on Site {
    siteMetadata {
      title
      description
      author
      siteUrl
    }
  }
`;

export const pageInfo = graphql`
  fragment PageInfo on MarkdownRemark {
    id
    excerpt(pruneLength: 160)
    frontmatter {
      title
      description
      date(formatString: "MMMM DD, YYYY")
    }
    fields {
      slug
    }
  }
`;
"""
        
        return files
    
    def _generate_component_test(self, comp_info) -> str:
        """Generate component test"""
        return f"""import React from 'react';
import {{ render, screen }} from '@testing-library/react';
import {comp_info['name']} from './{self._to_kebab_case(comp_info['name'])}';

describe('{comp_info['name']}', () => {{
  it('renders without crashing', () => {{
    render(<{comp_info['name']} />);
  }});
  
  it('displays content correctly', () => {{
    render(<{comp_info['name']} />);
    // Add specific test assertions here
  }});
}});
"""
    
    async def _generate_tests(self, components, context: ExportContext) -> Dict[str, str]:
        """Generate test files"""
        files = {}
        
        # Jest configuration
        files["jest.config.js"] = """module.exports = {
  transform: {
    '^.+\\\\.[jt]sx?$': '<rootDir>/jest-preprocess.js',
  },
  moduleNameMapping: {
    '.+\\\\.(css|styl|less|sass|scss)$': 'identity-obj-proxy',
    '.+\\\\.(jpg|jpeg|png|gif|eot|otf|webp|svg|ttf|woff|woff2|mp4|webm|wav|mp3|m4a|aac|oga)$':
      '<rootDir>/__mocks__/file-mock.js',
  },
  testPathIgnorePatterns: ['node_modules', '\\\\.cache', '<rootDir>.*/public'],
  transformIgnorePatterns: ['node_modules/(?!(gatsby)/)'],
  globals: {
    __PATH_PREFIX__: '',
  },
  testURL: 'http://localhost',
  setupFilesAfterEnv: ['<rootDir>/loadershim.js'],
};
"""
        
        # Jest preprocessor
        files["jest-preprocess.js"] = """const babelOptions = {
  presets: ['babel-preset-gatsby'],
};

module.exports = require('babel-jest').default.createTransformer(babelOptions);
"""
        
        # Setup file
        files["loadershim.js"] = """global.___loader = {
  enqueue: jest.fn(),
};
"""
        
        # Mock files
        files["__mocks__/file-mock.js"] = """module.exports = 'test-file-stub';
"""
        
        return files