-- ------------------------------------------------------------
-- Sequences (prefixo SQ_)
-- ------------------------------------------------------------
CREATE SEQUENCE SQ_USUARIOS START WITH 1 INCREMENT BY 1 NOCACHE NOCYCLE;
CREATE SEQUENCE SQ_CARREIRAS START WITH 1 INCREMENT BY 1 NOCACHE NOCYCLE;
CREATE SEQUENCE SQ_CURSOS START WITH 1 INCREMENT BY 1 NOCACHE NOCYCLE;
CREATE SEQUENCE SQ_USUARIO_CARREIRA START WITH 1 INCREMENT BY 1 NOCACHE NOCYCLE;
CREATE SEQUENCE SQ_USUARIO_CURSO START WITH 1 INCREMENT BY 1 NOCACHE NOCYCLE;

-- ------------------------------------------------------------
-- Tabela: USUARIOS
-- ------------------------------------------------------------
CREATE TABLE USUARIOS (
  usuario_id    NUMBER PRIMARY KEY,
  nome          VARCHAR2(200) NOT NULL,
  email         VARCHAR2(200) NOT NULL UNIQUE,
  senha         VARCHAR2(200) NOT NULL,
  data_criacao  DATE DEFAULT SYSDATE NOT NULL
);

-- Trigger para popular PK USUARIOS
CREATE OR REPLACE TRIGGER TRG_USUARIOS_AI
BEFORE INSERT ON USUARIOS
FOR EACH ROW
BEGIN
  IF :NEW.usuario_id IS NULL THEN
    SELECT SQ_USUARIOS.NEXTVAL INTO :NEW.usuario_id FROM DUAL;
  END IF;
  IF :NEW.data_criacao IS NULL THEN
    :NEW.data_criacao := SYSDATE;
  END IF;
END;
/
-- ------------------------------------------------------------
-- Tabela: CARREIRAS
-- ------------------------------------------------------------
CREATE TABLE CARREIRAS (
  carreira_id   NUMBER PRIMARY KEY,
  nome          VARCHAR2(200) NOT NULL,
  tipo          VARCHAR2(20) NOT NULL, -- INTEGRAR ou MIGRAR
  descricao     VARCHAR2(2000),
  CONSTRAINT CHK_CARREIRAS_TIPO CHECK (tipo IN ('INTEGRAR','MIGRAR'))
);

-- Trigger para popular PK CARREIRAS
CREATE OR REPLACE TRIGGER TRG_CARREIRAS_AI
BEFORE INSERT ON CARREIRAS
FOR EACH ROW
BEGIN
  IF :NEW.carreira_id IS NULL THEN
    SELECT SQ_CARREIRAS.NEXTVAL INTO :NEW.carreira_id FROM DUAL;
  END IF;
END;
/
-- ------------------------------------------------------------
-- Tabela: CURSOS
-- ------------------------------------------------------------
CREATE TABLE CURSOS (
  curso_id      NUMBER PRIMARY KEY,
  carreira_id   NUMBER NOT NULL,
  nome          VARCHAR2(300) NOT NULL,
  descricao     VARCHAR2(4000),
  ordem         NUMBER DEFAULT 1, -- ordem na trilha
  data_criacao  DATE DEFAULT SYSDATE NOT NULL,
  CONSTRAINT FK_CURSOS_CARREIRAS FOREIGN KEY (carreira_id) REFERENCES CARREIRAS(carreira_id)
);

-- Trigger para popular PK CURSOS
CREATE OR REPLACE TRIGGER TRG_CURSOS_AI
BEFORE INSERT ON CURSOS
FOR EACH ROW
BEGIN
  IF :NEW.curso_id IS NULL THEN
    SELECT SQ_CURSOS.NEXTVAL INTO :NEW.curso_id FROM DUAL;
  END IF;
  IF :NEW.data_criacao IS NULL THEN
    :NEW.data_criacao := SYSDATE;
  END IF;
END;
/
-- ------------------------------------------------------------
-- Tabela: USUARIO_CARREIRA (associação usuário <-> carreira)
-- ------------------------------------------------------------
CREATE TABLE USUARIO_CARREIRA (
  usuario_carreira_id NUMBER PRIMARY KEY,
  usuario_id          NUMBER NOT NULL,
  carreira_id         NUMBER NOT NULL,
  data_inicio         DATE DEFAULT SYSDATE NOT NULL,
  CONSTRAINT FK_UC_USUARIO FOREIGN KEY (usuario_id) REFERENCES USUARIOS(usuario_id) ON DELETE CASCADE,
  CONSTRAINT FK_UC_CARREIRA FOREIGN KEY (carreira_id) REFERENCES CARREIRAS(carreira_id) ON DELETE CASCADE
);

-- Trigger para popular PK USUARIO_CARREIRA
CREATE OR REPLACE TRIGGER TRG_USUARIO_CARREIRA_AI
BEFORE INSERT ON USUARIO_CARREIRA
FOR EACH ROW
BEGIN
  IF :NEW.usuario_carreira_id IS NULL THEN
    SELECT SQ_USUARIO_CARREIRA.NEXTVAL INTO :NEW.usuario_carreira_id FROM DUAL;
  END IF;
  IF :NEW.data_inicio IS NULL THEN
    :NEW.data_inicio := SYSDATE;
  END IF;
END;
/
-- ------------------------------------------------------------
-- Tabela: USUARIO_CURSO (associação usuário <-> curso) -> progresso
-- ------------------------------------------------------------
CREATE TABLE USUARIO_CURSO (
  usuario_curso_id NUMBER PRIMARY KEY,
  usuario_id       NUMBER NOT NULL,
  curso_id         NUMBER NOT NULL,
  status           VARCHAR2(20) DEFAULT 'NAO_INICIADO' NOT NULL, -- NAO_INICIADO, EM_ANDAMENTO, CONCLUIDO
  data_inicio      DATE,
  data_fim         DATE,
  CONSTRAINT CHK_USUARIO_CURSO_STATUS CHECK (status IN ('NAO_INICIADO','EM_ANDAMENTO','CONCLUIDO')),
  CONSTRAINT FK_UCUR_USUARIO FOREIGN KEY (usuario_id) REFERENCES USUARIOS(usuario_id) ON DELETE CASCADE,
  CONSTRAINT FK_UCUR_CURSO FOREIGN KEY (curso_id) REFERENCES CURSOS(curso_id) ON DELETE CASCADE,
  CONSTRAINT UQ_UCUR_USUARIO_CURSO UNIQUE (usuario_id, curso_id)
);

-- Trigger para popular PK USUARIO_CURSO e data_inicio default ao inserir quando status != NAO_INICIADO
CREATE OR REPLACE TRIGGER TRG_USUARIO_CURSO_AI
BEFORE INSERT ON USUARIO_CURSO
FOR EACH ROW
BEGIN
  IF :NEW.usuario_curso_id IS NULL THEN
    SELECT SQ_USUARIO_CURSO.NEXTVAL INTO :NEW.usuario_curso_id FROM DUAL;
  END IF;

  -- Se inserir e o status já for EM_ANDAMENTO, define data_inicio se não especificada
  IF :NEW.data_inicio IS NULL AND :NEW.status = 'EM_ANDAMENTO' THEN
    :NEW.data_inicio := SYSDATE;
  END IF;

  -- Se inserir com NAO_INICIADO, deixa data_inicio NULL (só quando começar vira data)
  -- Se inserir com CONCLUIDO (cenário improvável no insert), seta data_inicio e data_fim se não existirem
  IF :NEW.status = 'CONCLUIDO' THEN
    IF :NEW.data_inicio IS NULL THEN
      :NEW.data_inicio := SYSDATE;
    END IF;
    IF :NEW.data_fim IS NULL THEN
      :NEW.data_fim := SYSDATE;
    END IF;
  END IF;
END;
/
-- ------------------------------------------------------------
-- Trigger para atualizar data_inicio/data_fim em UPDATE de status
-- - Se status muda para EM_ANDAMENTO e data_inicio é NULL -> set data_inicio = SYSDATE
-- - Se status muda para CONCLUIDO e data_fim é NULL -> set data_fim = SYSDATE
-- ------------------------------------------------------------
CREATE OR REPLACE TRIGGER TRG_USUARIO_CURSO_AU
BEFORE UPDATE OF status ON USUARIO_CURSO
FOR EACH ROW
BEGIN
  -- Mudou para EM_ANDAMENTO
  IF :NEW.status = 'EM_ANDAMENTO' AND (:OLD.status IS NULL OR :OLD.status != 'EM_ANDAMENTO') THEN
    IF :NEW.data_inicio IS NULL THEN
      :NEW.data_inicio := SYSDATE;
    END IF;
    :NEW.data_fim := NULL; -- garantir que data_fim seja nula enquanto em andamento
  END IF;

  -- Mudou para CONCLUIDO
  IF :NEW.status = 'CONCLUIDO' AND (:OLD.status IS NULL OR :OLD.status != 'CONCLUIDO') THEN
    IF :NEW.data_inicio IS NULL THEN
      :NEW.data_inicio := SYSDATE; -- caso não existisse
    END IF;
    IF :NEW.data_fim IS NULL THEN
      :NEW.data_fim := SYSDATE;
    END IF;
  END IF;

  -- Se regravou para NAO_INICIADO, limpa as datas
  IF :NEW.status = 'NAO_INICIADO' THEN
    :NEW.data_inicio := NULL;
    :NEW.data_fim := NULL;
  END IF;
END;
/
-- ------------------------------------------------------------
-- Índices sugeridos (opcionais, melhoram performance nas consultas)
-- ------------------------------------------------------------
CREATE INDEX IDX_CURSOS_NOME ON CURSOS(LOWER(nome));
CREATE INDEX IDX_CURSOS_DATA_CRIACAO ON CURSOS(data_criacao);
CREATE INDEX IDX_USUARIO_CURSO_USUARIO ON USUARIO_CURSO(usuario_id);
CREATE INDEX IDX_USUARIO_CURSO_CURSO ON USUARIO_CURSO(curso_id);

-- ------------------------------------------------------------
-- Exemplo de grants (opcional) - adapte ao seu schema/usuário se necessário
-- ------------------------------------------------------------
-- GRANT SELECT, INSERT, UPDATE, DELETE ON USUARIOS TO SEU_USUARIO;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON CARREIRAS TO SEU_USUARIO;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON CURSOS TO SEU_USUARIO;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON USUARIO_CARREIRA TO SEU_USUARIO;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON USUARIO_CURSO TO SEU_USUARIO;
