import React from "react";
import { Container } from "react-bootstrap";

const About = () => {
  return (
    <Container className="mt-5">
      <h2>About Us</h2>
      <p>
        BYB 입니다, 인공지능 챗봇 기반 서비스를 제공합니다.
        <hr></hr>
      </p>
      <h3>Server Programming</h3>
      <br></br>
      <p>Course DescriptionThis course aims to provide students with a comprehensive understanding of server programming, from basic concepts to practical skills applicable in real-world scenarios. This course covers various topics related to the design and implementation of server programs based on Linux systems and the C programming language, and includes hands-on practice through actual projects.</p>
    </Container>
  );
};

export default About;