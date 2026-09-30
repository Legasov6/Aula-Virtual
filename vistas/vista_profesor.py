import customtkinter as ctk
import psycopg2
from conexion import conectar_bd

BG_COLOR = "#282828"
SIDEBAR_COLOR = "#3c3836"
ACCENT_COLOR = "#d79921"
TEXT_COLOR = "#ebdbb2"
RED_COLOR = "#cc241d"
GREEN_COLOR = "#98971a"
BLUE_COLOR = "#458588"

# ==========================================
# VENTANA MODAL: PLAN DE EVALUACIÓN
# ==========================================
class VentanaEvaluaciones(ctk.CTkToplevel):
    def __init__(self, master, id_seccion, nombre_clase):
        super().__init__(master)
        self.title(f"Plan de Evaluación: {nombre_clase}")
        self.geometry("550x550")
        self.configure(fg_color=BG_COLOR)
        self.grab_set()
        
        self.id_seccion = id_seccion
        self.peso_actual = 0.0

        ctk.CTkLabel(self, text=f"Evaluaciones:\n{nombre_clase}", font=ctk.CTkFont(size=18, weight="bold"), text_color=ACCENT_COLOR).pack(pady=(15, 5))
        
        self.lbl_peso = ctk.CTkLabel(self, text="Total acumulado: 0% / 100%", font=ctk.CTkFont(size=14, weight="bold"), text_color=TEXT_COLOR)
        self.lbl_peso.pack(pady=(0, 10))

        # Formulario
        frame_form = ctk.CTkFrame(self, fg_color="transparent")
        frame_form.pack(fill="x", padx=20)

        self.ent_desc = ctk.CTkEntry(frame_form, placeholder_text="Descripción (Ej: Parcial 1)", width=220, fg_color=SIDEBAR_COLOR, text_color=TEXT_COLOR)
        self.ent_desc.grid(row=0, column=0, padx=5, pady=5)

        self.ent_peso = ctk.CTkEntry(frame_form, placeholder_text="Peso % (Ej: 25)", width=120, justify="center", fg_color=SIDEBAR_COLOR, text_color=TEXT_COLOR)
        self.ent_peso.grid(row=0, column=1, padx=5, pady=5)

        btn_agregar = ctk.CTkButton(frame_form, text="+ Añadir", width=80, fg_color=GREEN_COLOR, text_color=BG_COLOR, font=ctk.CTkFont(weight="bold"), command=self.agregar_evaluacion)
        btn_agregar.grid(row=0, column=2, padx=5, pady=5)

        self.lbl_error = ctk.CTkLabel(self, text="", text_color=RED_COLOR)
        self.lbl_error.pack(pady=5)

        # Tabla
        self.tabla_eval = ctk.CTkScrollableFrame(self, fg_color=SIDEBAR_COLOR)
        self.tabla_eval.pack(padx=20, pady=5, fill="both", expand=True)
        self.tabla_eval.grid_columnconfigure((0,1), weight=1)
        self.tabla_eval.grid_columnconfigure(2, weight=0)

        self.cargar_evaluaciones()

    def agregar_evaluacion(self):
        desc = self.ent_desc.get().strip()
        peso_str = self.ent_peso.get().strip()

        if not desc or not peso_str:
            self.lbl_error.configure(text="Llena ambos campos.", text_color=RED_COLOR)
            return

        try:
            peso = float(peso_str)
            if peso <= 0: raise ValueError
        except ValueError:
            self.lbl_error.configure(text="El peso debe ser un número mayor a 0.", text_color=RED_COLOR)
            return

        if self.peso_actual + peso > 100.0:
            self.lbl_error.configure(text=f"¡Límite excedido! Solo te queda {100.0 - self.peso_actual}% disponible.", text_color=RED_COLOR)
            return

        conn, cur = conectar_bd()
        if conn:
            try:
                cur.execute("INSERT INTO evaluacion (descripcion, ponderacion, id_seccion) VALUES (%s, %s, %s)", 
                            (desc, peso, self.id_seccion))
                conn.commit()
                self.ent_desc.delete(0, 'end')
                self.ent_peso.delete(0, 'end')
                self.lbl_error.configure(text="Evaluación añadida.", text_color=GREEN_COLOR)
                self.cargar_evaluaciones()
            except psycopg2.errors.CheckViolation:
                conn.rollback()
                self.lbl_error.configure(text="Error: El peso debe estar entre 0.01 y 100.", text_color=RED_COLOR)
            except Exception as e:
                conn.rollback()
                self.lbl_error.configure(text=f"Error: {e}", text_color=RED_COLOR)
            finally:
                cur.close()
                conn.close()

    def cargar_evaluaciones(self):
        for widget in self.tabla_eval.winfo_children():
            widget.destroy()

        encabezados = ["Descripción", "Ponderación (%)", "Acciones"]
        for i, txt in enumerate(encabezados):
            ctk.CTkLabel(self.tabla_eval, text=txt, font=ctk.CTkFont(weight="bold"), text_color=ACCENT_COLOR).grid(row=0, column=i, padx=5, pady=5, sticky="w")

        conn, cur = conectar_bd()
        if conn:
            try:
                cur.execute("SELECT id_evaluacion, descripcion, ponderacion FROM evaluacion WHERE id_seccion = %s ORDER BY id_evaluacion", (self.id_seccion,))
                filas = cur.fetchall()
                
                # ¡AQUÍ ESTÁ LA MAGIA! Convertimos f[2] a float para que no pelee con Python
                self.peso_actual = sum([float(f[2]) for f in filas])
                
                color_peso = GREEN_COLOR if self.peso_actual == 100.0 else TEXT_COLOR
                self.lbl_peso.configure(text=f"Total acumulado: {self.peso_actual}% / 100%", text_color=color_peso)

                if not filas:
                    ctk.CTkLabel(self.tabla_eval, text="No hay evaluaciones registradas.", text_color=TEXT_COLOR).grid(row=1, column=0, columnspan=3, pady=20)

                for fila, (id_ev, desc, peso) in enumerate(filas, start=1):
                    ctk.CTkLabel(self.tabla_eval, text=desc, text_color=TEXT_COLOR).grid(row=fila, column=0, padx=5, pady=2, sticky="w")
                    ctk.CTkLabel(self.tabla_eval, text=f"{peso}%", text_color=TEXT_COLOR).grid(row=fila, column=1, padx=5, pady=2, sticky="w")
                    
                    btn_borrar = ctk.CTkButton(self.tabla_eval, text="X", width=30, fg_color=RED_COLOR, text_color=TEXT_COLOR, command=lambda e=id_ev: self.borrar_evaluacion(e))
                    btn_borrar.grid(row=fila, column=2, padx=5, pady=2, sticky="e")
            except Exception as e:
                print("Error cargando evaluaciones:", e)
            finally:
                cur.close()
                conn.close()

    def borrar_evaluacion(self, id_evaluacion):
        conn, cur = conectar_bd()
        if conn:
            try:
                cur.execute("DELETE FROM evaluacion WHERE id_evaluacion = %s", (id_evaluacion,))
                conn.commit()
                self.lbl_error.configure(text="")
                self.cargar_evaluaciones()
            except Exception as e:
                conn.rollback()
                print("Error borrando:", e)
            finally:
                cur.close()
                conn.close()

# ==========================================
# VENTANA MODAL: CARGAR NOTAS
# ==========================================
class VentanaCalificaciones(ctk.CTkToplevel):
    def __init__(self, master, id_seccion, nombre_clase):
        super().__init__(master)
        self.title(f"Calificaciones: {nombre_clase}")
        self.geometry("850x600")
        self.configure(fg_color=BG_COLOR)
        self.grab_set()

        self.id_seccion = id_seccion

        ctk.CTkLabel(self, text=f"Registro de Notas:\n{nombre_clase}", font=ctk.CTkFont(size=18, weight="bold"), text_color=ACCENT_COLOR).pack(pady=(15, 5))

        frame_top = ctk.CTkFrame(self, fg_color="transparent")
        frame_top.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(frame_top, text="Seleccionar Evaluación:", text_color=TEXT_COLOR).pack(side="left", padx=5)
        self.combo_eval = ctk.CTkOptionMenu(frame_top, width=250, fg_color=SIDEBAR_COLOR, text_color=TEXT_COLOR, button_color=ACCENT_COLOR, command=self.al_cambiar_evaluacion)
        self.combo_eval.pack(side="left", padx=5)

        self.lbl_msj = ctk.CTkLabel(frame_top, text="", text_color=GREEN_COLOR)
        self.lbl_msj.pack(side="right", padx=10)

        self.tabla_notas = ctk.CTkScrollableFrame(self, fg_color=SIDEBAR_COLOR)
        self.tabla_notas.pack(padx=20, pady=5, fill="both", expand=True)
        self.tabla_notas.grid_columnconfigure((0,1), weight=1)
        self.tabla_notas.grid_columnconfigure((2,3,4), weight=0)

        self.mapa_evaluaciones = {}
        self.cargar_opciones_evaluaciones()

    def cargar_opciones_evaluaciones(self):
        conn, cur = conectar_bd()
        if conn:
            try:
                cur.execute("SELECT id_evaluacion, descripcion, ponderacion FROM evaluacion WHERE id_seccion = %s ORDER BY id_evaluacion", (self.id_seccion,))
                evaluaciones = cur.fetchall()
                if evaluaciones:
                    opciones = []
                    for id_ev, desc, peso in evaluaciones:
                        texto = f"{desc} ({peso}%)"
                        opciones.append(texto)
                        self.mapa_evaluaciones[texto] = id_ev
                    
                    self.combo_eval.configure(values=opciones)
                    self.combo_eval.set(opciones[0])
                    self.cargar_lista_alumnos()
                else:
                    self.combo_eval.configure(values=["No hay evaluaciones creadas"], state="disabled")
                    self.combo_eval.set("No hay evaluaciones creadas")
                    ctk.CTkLabel(self.tabla_notas, text="Primero debes crear un Plan de Evaluación.", text_color=RED_COLOR).grid(row=0, column=0, pady=20)
            except Exception as e:
                print("Error cargando combo de evaluaciones:", e)
            finally:
                cur.close()
                conn.close()

    def al_cambiar_evaluacion(self, seleccion):
        self.lbl_msj.configure(text="")
        self.cargar_lista_alumnos()

    def cargar_lista_alumnos(self):
        for widget in self.tabla_notas.winfo_children():
            widget.destroy()

        seleccion = self.combo_eval.get()
        if seleccion not in self.mapa_evaluaciones: return
        id_evaluacion = self.mapa_evaluaciones[seleccion]

        encabezados = ["Cédula", "Estudiante", "Nota (1-10)", "Estado", "Acción"]
        for i, txt in enumerate(encabezados):
            ctk.CTkLabel(self.tabla_notas, text=txt, font=ctk.CTkFont(weight="bold"), text_color=ACCENT_COLOR).grid(row=0, column=i, padx=5, pady=10, sticky="w")

        conn, cur = conectar_bd()
        if conn:
            try:
                query = '''
                    SELECT e.id_estudiante, e.cedula, e.apellidos, e.nombres,
                           c.id_calificacion, c.nota_numerica, c.nota_conceptual
                    FROM inscripcion i
                    JOIN estudiante e ON i.id_estudiante = e.id_estudiante
                    LEFT JOIN calificacion c ON e.id_estudiante = c.id_estudiante AND c.id_evaluacion = %s
                    WHERE i.id_seccion = %s
                    ORDER BY e.apellidos, e.nombres
                '''
                cur.execute(query, (id_evaluacion, self.id_seccion))
                alumnos = cur.fetchall()

                if not alumnos:
                    ctk.CTkLabel(self.tabla_notas, text="No hay alumnos inscritos en esta sección.", text_color=TEXT_COLOR).grid(row=1, column=0, columnspan=5, pady=20)

                for fila, (id_est, cedula, apellidos, nombres, id_calif, nota_num, nota_con) in enumerate(alumnos, start=1):
                    ctk.CTkLabel(self.tabla_notas, text=cedula, text_color=TEXT_COLOR).grid(row=fila, column=0, padx=5, pady=5, sticky="w")
                    ctk.CTkLabel(self.tabla_notas, text=f"{apellidos}, {nombres}", text_color=TEXT_COLOR).grid(row=fila, column=1, padx=5, pady=5, sticky="w")
                    
                    # Entry para la nota numérica
                    ent_nota = ctk.CTkEntry(self.tabla_notas, width=80, justify="center", fg_color=BG_COLOR, text_color=TEXT_COLOR)
                    ent_nota.grid(row=fila, column=2, padx=5, pady=5, sticky="w")
                    if nota_num is not None:
                        ent_nota.insert(0, str(nota_num))

                    # Combobox para el concepto
                    cb_estado = ctk.CTkComboBox(self.tabla_notas, values=["Aprobado", "Reprobado"], width=120, fg_color=BG_COLOR, button_color=ACCENT_COLOR)
                    cb_estado.grid(row=fila, column=3, padx=5, pady=5, sticky="w")
                    cb_estado.set(nota_con if nota_con else "Reprobado")

                    texto_btn = "Actualizar" if id_calif else "Guardar"
                    color_btn = BLUE_COLOR if id_calif else GREEN_COLOR
                    
                    # Pasamos los widgets directamente al lambda para extraer sus valores en la función
                    btn_guardar = ctk.CTkButton(self.tabla_notas, text=texto_btn, width=70, fg_color=color_btn, text_color=BG_COLOR, font=ctk.CTkFont(weight="bold"),
                                                command=lambda e=id_est, c=id_calif, ent=ent_nota, cb=cb_estado: self.guardar_nota(e, c, ent, cb, id_evaluacion))
                    btn_guardar.grid(row=fila, column=4, padx=5, pady=5, sticky="e")

            except Exception as e:
                print("Error cargando alumnos para notas:", e)
            finally:
                cur.close()
                conn.close()

    def guardar_nota(self, id_estudiante, id_calificacion, ent_nota, cb_estado, id_evaluacion):
        nota_str = ent_nota.get().strip()
        concepto = cb_estado.get()

        if not nota_str:
            self.lbl_msj.configure(text="La nota no puede estar vacía.", text_color=RED_COLOR)
            return

        try:
            nota_num = float(nota_str)
            if nota_num < 1 or nota_num > 10:
                self.lbl_msj.configure(text="La nota debe ser entre 1 y 10.", text_color=RED_COLOR)
                return
        except ValueError:
            self.lbl_msj.configure(text="Ingresa una nota numérica válida.", text_color=RED_COLOR)
            return

        conn, cur = conectar_bd()
        if conn:
            try:
                if id_calificacion:
                    cur.execute("UPDATE calificacion SET nota_numerica=%s, nota_conceptual=%s WHERE id_calificacion=%s", (nota_num, concepto, id_calificacion))
                else:
                    cur.execute("INSERT INTO calificacion (id_estudiante, id_evaluacion, nota_numerica, nota_conceptual) VALUES (%s, %s, %s, %s)", 
                                (id_estudiante, id_evaluacion, nota_num, concepto))
                conn.commit()
                self.lbl_msj.configure(text="¡Nota guardada con éxito!", text_color=GREEN_COLOR)
                
                # Recargar sutilmente para actualizar el botón de Guardar a Actualizar
                self.cargar_lista_alumnos() 
            except Exception as e:
                conn.rollback()
                self.lbl_msj.configure(text=f"Error: {e}", text_color=RED_COLOR)
            finally:
                cur.close()
                conn.close()

# ==========================================
# PANEL PRINCIPAL: VISTA PROFESOR
# ==========================================
class VistaProfesor(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=BG_COLOR)
        
        # --- HEADER / SIMULADOR DE SESIÓN ---
        frame_header = ctk.CTkFrame(self, fg_color="transparent")
        frame_header.pack(fill="x", padx=20, pady=(20, 10))

        frame_top = ctk.CTkFrame(frame_header, fg_color="transparent")
        frame_top.pack(fill="x")
        
        ctk.CTkLabel(frame_top, text="Portal Docente", font=ctk.CTkFont(size=24, weight="bold"), text_color=TEXT_COLOR).pack(side="left")
        self.lbl_periodo = ctk.CTkLabel(frame_top, text="Periodo: Cargando...", font=ctk.CTkFont(weight="bold"), text_color=ACCENT_COLOR)
        self.lbl_periodo.pack(side="right", padx=10)

        frame_ctrl = ctk.CTkFrame(frame_header, fg_color="transparent")
        frame_ctrl.pack(fill="x", pady=(10, 0))

        ctk.CTkLabel(frame_ctrl, text="Simulando sesión de:", text_color=TEXT_COLOR).pack(side="left", padx=(0, 5))
        self.combo_profesor = ctk.CTkOptionMenu(frame_ctrl, width=250, fg_color=SIDEBAR_COLOR, text_color=TEXT_COLOR, button_color=ACCENT_COLOR, command=self.al_cambiar_profesor)
        self.combo_profesor.pack(side="left")

        # --- CONTENIDO: MIS SECCIONES ---
        ctk.CTkLabel(self, text="Mis Clases Asignadas", font=ctk.CTkFont(size=18, weight="bold"), text_color=TEXT_COLOR).pack(pady=(10, 5))

        self.tabla_secciones = ctk.CTkScrollableFrame(self, fg_color=SIDEBAR_COLOR)
        self.tabla_secciones.pack(padx=20, pady=5, fill="both", expand=True)
        self.tabla_secciones.grid_columnconfigure((0,1,2), weight=1)
        self.tabla_secciones.grid_columnconfigure(3, weight=0)

        self.id_profesor_actual = None
        self.id_periodo_activo = None
        self.mapa_profesores = {}

        self.inicializar_datos()

    def inicializar_datos(self):
        conn, cur = conectar_bd()
        if conn:
            try:
                cur.execute("SELECT id_periodo, codigo_periodo FROM periodo WHERE estado = 'Activo'")
                periodo = cur.fetchone()
                if periodo:
                    self.id_periodo_activo = periodo[0]
                    self.lbl_periodo.configure(text=f"Periodo Activo: {periodo[1]}")
                else:
                    self.lbl_periodo.configure(text="No hay periodo activo", text_color=RED_COLOR)

                cur.execute("SELECT id_profesor, cedula, nombres, apellidos FROM profesor ORDER BY apellidos")
                profesores = cur.fetchall()
                if profesores:
                    opciones = []
                    for id_p, ced, nom, ape in profesores:
                        texto = f"Prof. {ape}, {nom} ({ced})"
                        opciones.append(texto)
                        self.mapa_profesores[texto] = id_p
                    
                    self.combo_profesor.configure(values=opciones)
                    self.combo_profesor.set(opciones[0])
                    self.al_cambiar_profesor(opciones[0])
                else:
                    self.combo_profesor.configure(values=["No hay docentes registrados"])
                    self.combo_profesor.set("No hay docentes registrados")

            except Exception as e:
                print("Error de inicialización:", e)
            finally:
                cur.close()
                conn.close()

    def al_cambiar_profesor(self, seleccion):
        if seleccion in self.mapa_profesores:
            self.id_profesor_actual = self.mapa_profesores[seleccion]
            self.cargar_secciones()

    def cargar_secciones(self):
        for widget in self.tabla_secciones.winfo_children():
            widget.destroy()

        if not self.id_profesor_actual or not self.id_periodo_activo: return

        encabezados = ["Materia", "Sec.", "Horario", "Inscritos", "Gestión Académica"]
        for i, texto in enumerate(encabezados):
            ctk.CTkLabel(self.tabla_secciones, text=texto, font=ctk.CTkFont(weight="bold"), text_color=ACCENT_COLOR).grid(row=0, column=i, padx=5, pady=10, sticky="w")

        conn, cur = conectar_bd()
        if conn:
            try:
                query = '''
                    SELECT s.id_seccion, c.nombre, s.identificador, c.cupo_maximo,
                           (SELECT COUNT(*) FROM inscripcion i WHERE i.id_seccion = s.id_seccion) as inscritos,
                           COALESCE(array_to_string(array_agg(h.dia_semana || ' ' || substr(h.hora_inicio::text, 1, 5) || '-' || substr(h.hora_fin::text, 1, 5) ORDER BY h.id_horario), ' | '), 'Sin asignar') as horario_str
                    FROM seccion s
                    JOIN curso c ON s.id_curso = c.id_curso
                    LEFT JOIN horario h ON s.id_seccion = h.id_seccion
                    WHERE s.id_profesor = %s AND s.id_periodo = %s
                    GROUP BY s.id_seccion, c.nombre, c.cupo_maximo
                    ORDER BY c.nombre, s.identificador
                '''
                cur.execute(query, (self.id_profesor_actual, self.id_periodo_activo))
                secciones = cur.fetchall()

                if not secciones:
                    ctk.CTkLabel(self.tabla_secciones, text="No tienes secciones asignadas este periodo.", text_color=TEXT_COLOR).grid(row=1, column=0, columnspan=5, pady=20)

                for fila_idx, (id_sec, curso, ident, cupo_max, inscritos, horario) in enumerate(secciones, start=1):
                    ctk.CTkLabel(self.tabla_secciones, text=curso, text_color=TEXT_COLOR).grid(row=fila_idx, column=0, padx=5, pady=5, sticky="w")
                    ctk.CTkLabel(self.tabla_secciones, text=ident, text_color=TEXT_COLOR).grid(row=fila_idx, column=1, padx=5, pady=5, sticky="w")
                    ctk.CTkLabel(self.tabla_secciones, text=horario, text_color=TEXT_COLOR).grid(row=fila_idx, column=2, padx=5, pady=5, sticky="w")
                    ctk.CTkLabel(self.tabla_secciones, text=f"{inscritos} / {cupo_max}", text_color=TEXT_COLOR).grid(row=fila_idx, column=3, padx=5, pady=5, sticky="w")

                    frame_acc = ctk.CTkFrame(self.tabla_secciones, fg_color="transparent")
                    frame_acc.grid(row=fila_idx, column=4, padx=5, pady=5, sticky="e")

                    nom_completo = f"{curso} ({ident})"
                    
                    btn_eval = ctk.CTkButton(frame_acc, text="Plan de Evaluación", width=120, fg_color=ACCENT_COLOR, text_color=BG_COLOR, command=lambda s=id_sec, n=nom_completo: VentanaEvaluaciones(self, s, n))
                    btn_eval.pack(side="left", padx=2)

                    btn_notas = ctk.CTkButton(frame_acc, text="Cargar Notas", width=100, fg_color=BLUE_COLOR, text_color=TEXT_COLOR, command=lambda s=id_sec, n=nom_completo: VentanaCalificaciones(self, s, n))
                    btn_notas.pack(side="left", padx=2)

            except Exception as e:
                print("Error cargando mis secciones:", e)
            finally:
                cur.close()
                conn.close()