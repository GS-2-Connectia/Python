----------------------------------------------------

INSERT INTO USUARIOS (nome, email, senha)
VALUES ('João Silva', 'joao@example.com', '123');

INSERT INTO USUARIOS (nome, email, senha)
VALUES ('Maria Souza', 'maria@example.com', '456');

----------------------------------------------------

INSERT INTO CARREIRAS (nome, tipo, descricao)
VALUES ('Arquitetura', 'INTEGRAR', 'Trilha para arquitetos que querem integrar programação.');

INSERT INTO CARREIRAS (nome, tipo, descricao)
VALUES ('Marketing Digital', 'INTEGRAR', 'Trilha para profissionais de marketing que desejam usar programação.');

INSERT INTO CARREIRAS (nome, tipo, descricao)
VALUES ('Desenvolvimento Full-Stack', 'MIGRAR', 'Trilha completa para mudança de carreira.');

----------------------------------------------------

-- Carreira 1 (Arquitetura)
INSERT INTO CURSOS (carreira_id, nome, descricao, ordem)
VALUES (1, 'Introdução à Programação para Arquitetos', 'Lógica aplicada a arquitetura.', 1);

INSERT INTO CURSOS (carreira_id, nome, descricao, ordem)
VALUES (1, 'Automação de Projetos com Python', 'Automatização de tarefas CAD.', 2);

-- Carreira 2 (Marketing)
INSERT INTO CURSOS (carreira_id, nome, descricao, ordem)
VALUES (2, 'Python para Marketing', 'Automação e análise de campanhas.', 1);

-- Carreira 3 (Full Stack)
INSERT INTO CURSOS (carreira_id, nome, descricao, ordem)
VALUES (3, 'HTML e CSS', 'Fundamentos para iniciar na área.', 1);

INSERT INTO CURSOS (carreira_id, nome, descricao, ordem)
VALUES (3, 'Lógica de Programação', 'Base essencial.', 2);


----------------------------------------------------

INSERT INTO USUARIO_CARREIRA (usuario_id, carreira_id)
VALUES (1, 3);  -- João escolheu Full Stack

INSERT INTO USUARIO_CARREIRA (usuario_id, carreira_id)
VALUES (2, 1);  -- Maria escolheu Arquitetura

----------------------------------------------------

-- João em andamento no curso HTML/CSS (curso_id = 4)
INSERT INTO USUARIO_CURSO (usuario_id, curso_id, status)
VALUES (1, 4, 'EM_ANDAMENTO');

-- João ainda não iniciou Lógica
INSERT INTO USUARIO_CURSO (usuario_id, curso_id, status)
VALUES (1, 5, 'NAO_INICIADO');

-- Maria concluiu curso 1
INSERT INTO USUARIO_CURSO (usuario_id, curso_id, status)
VALUES (2, 1, 'CONCLUIDO');
