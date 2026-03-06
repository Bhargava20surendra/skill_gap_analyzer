CREATE DATABASE skill_gap_analyzer;
USE skill_gap_analyzer;

CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE job_roles (
    role_id INT AUTO_INCREMENT PRIMARY KEY,
    role_name VARCHAR(100) NOT NULL
);

INSERT INTO job_roles (role_name) VALUES
('Data Analyst'),
('Web Developer'),
('Software Engineer'),
('Machine Learning Engineer'),
('DevOps Engineer');

CREATE TABLE skills (
    skill_id INT AUTO_INCREMENT PRIMARY KEY,
    skill_name VARCHAR(100) UNIQUE NOT NULL
);

INSERT INTO skills (skill_name) VALUES
('Python'),
('Java'),
('SQL'),
('HTML'),
('CSS'),
('JavaScript'),
('Machine Learning'),
('Deep Learning'),
('Power BI'),
('Excel'),
('Docker'),
('Git'),
('Statistics');

CREATE TABLE job_role_skills (
    id INT AUTO_INCREMENT PRIMARY KEY,
    role_id INT,
    skill_id INT,
    FOREIGN KEY (role_id) REFERENCES job_roles(role_id),
    FOREIGN KEY (skill_id) REFERENCES skills(skill_id)
);


INSERT INTO job_role_skills (role_id, skill_id) VALUES
(1,1),
(1,3),
(1,9),
(1,10),
(1,13),

(2,4),
(2,5),
(2,6),
(2,1),

(3,1),
(3,3),
(3,12),
(3,11);



CREATE TABLE extracted_skills (
    id INT AUTO_INCREMENT PRIMARY KEY,
    resume_id INT,
    skill_id INT,
    FOREIGN KEY (resume_id) REFERENCES resumes(resume_id),
    FOREIGN KEY (skill_id) REFERENCES skills(skill_id)
);


CREATE TABLE resumes (
    resume_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    file_name VARCHAR(255),
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE skill_gap_results (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    role_id INT,
    missing_skill_id INT,
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (role_id) REFERENCES job_roles(role_id),
    FOREIGN KEY (missing_skill_id) REFERENCES skills(skill_id)
);

CREATE TABLE analysis_history (
    analysis_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    resume_id INT,
    role_id INT,
    analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (resume_id) REFERENCES resumes(resume_id),
    FOREIGN KEY (role_id) REFERENCES job_roles(role_id)
);

SELECT s.skill_name
FROM job_role_skills jrs
JOIN skills s ON jrs.skill_id = s.skill_id
WHERE jrs.role_id = 1
AND s.skill_id NOT IN (
    SELECT skill_id
    FROM extracted_skills
    WHERE resume_id = 1
);

SELECT s.skill_name
FROM extracted_skills es
JOIN skills s ON es.skill_id = s.skill_id
WHERE es.resume_id = 1;


SELECT s.skill_name
FROM job_role_skills jrs
JOIN skills s ON jrs.skill_id = s.skill_id
WHERE jrs.role_id = 1;


INSERT INTO skill_gap_results (user_id, role_id, missing_skill_id)
VALUES (1, 1, 9);

SELECT s.skill_name
FROM skill_gap_results sgr
JOIN skills s ON sgr.missing_skill_id = s.skill_id
WHERE sgr.user_id = 1 AND sgr.role_id = 1;

