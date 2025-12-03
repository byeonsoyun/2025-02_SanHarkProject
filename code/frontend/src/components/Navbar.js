import React from "react";
import { Link, useLocation } from "react-router-dom";
import { Navbar, Nav, Container } from "react-bootstrap";

const NavbarComp = () => {
  const location = useLocation();

  return (
    <Navbar bg="primary" variant="dark" expand="lg" sticky="top">
      <Container>
        <Navbar.Brand as={Link} to="/" style={{fontWeight: 'bold'}}>
          🎓 충북대 공지사항 챗봇
        </Navbar.Brand>
        <Navbar.Toggle aria-controls="basic-navbar-nav" />
        <Navbar.Collapse id="basic-navbar-nav">
          <Nav className="ms-auto">
            <Nav.Link as={Link} to="/" active={location.pathname === "/"}>
              홈
            </Nav.Link>
            <Nav.Link as={Link} to="/chat" active={location.pathname === "/chat"}>
              챗봇
            </Nav.Link>
            <Nav.Link as={Link} to="/calendar" active={location.pathname === "/calendar"}>
              📅 학사일정
            </Nav.Link>
            <Nav.Link as={Link} to="/about" active={location.pathname === "/about"}>
              서비스 소개
            </Nav.Link>
          </Nav>
        </Navbar.Collapse>
      </Container>
    </Navbar>
  );
};

export default NavbarComp;
