import React, { useState, useEffect } from "react";
import { Link, useLocation } from "react-router-dom";
import { Navbar, Nav, Container } from "react-bootstrap";
import { useTheme } from "../App";

const NavbarComp = () => {
  const location = useLocation();
  const { theme, toggleTheme } = useTheme();
  const [expanded, setExpanded] = useState(false);

  const navbarBg = theme === 'dark' ? '#1a1a1a' : '#C8102E';
  const navbarVariant = 'dark';

  // 메뉴가 열리면 4초 후 자동으로 닫기
  useEffect(() => {
    if (expanded) {
      const timer = setTimeout(() => {
        setExpanded(false);
      }, 4000);
      
      return () => clearTimeout(timer);
    }
  }, [expanded]);

  return (
    <Navbar 
      expand="lg" 
      sticky="top" 
      style={{ backgroundColor: navbarBg }}
      expanded={expanded}
      onToggle={setExpanded}
    >
      <Container>
        <Navbar.Brand as={Link} to="/" style={{ color: '#fff', fontWeight: 'bold' }}>
          🎓 소왕이
        </Navbar.Brand>
        <Navbar.Toggle aria-controls="basic-navbar-nav" />
        <Navbar.Collapse id="basic-navbar-nav">
          <Nav className="ms-auto">
            <Nav.Link 
              as={Link} 
              to="/" 
              active={location.pathname === "/"}
              style={{ color: '#fff' }}
              onClick={() => setExpanded(false)}
            >
              홈
            </Nav.Link>
            <Nav.Link 
              as={Link} 
              to="/chat" 
              active={location.pathname === "/chat"}
              style={{ color: '#fff' }}
              onClick={() => setExpanded(false)}
            >
              챗봇
            </Nav.Link>
            <Nav.Link 
              as={Link} 
              to="/calendar" 
              active={location.pathname === "/calendar"}
              style={{ color: '#fff' }}
              onClick={() => setExpanded(false)}
            >
              캘린더
            </Nav.Link>
            <Nav.Link 
              onClick={() => {
                toggleTheme();
                setExpanded(false);
              }}
              style={{ color: '#fff', cursor: 'pointer' }}
            >
              {theme === 'dark' ? '☀️' : '🌙'}
            </Nav.Link>
          </Nav>
        </Navbar.Collapse>
      </Container>
    </Navbar>
  );
};

export default NavbarComp;
