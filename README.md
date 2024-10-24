\documentclass{article}
\usepackage{graphicx} % Para incluir imágenes
\usepackage{float}    % Para usar el modificador [H]

\begin{document}

\section{Informe de Pruebas}
Durante las pruebas del sistema, se llevaron a cabo varias simulaciones para evaluar la funcionalidad del sistema ante la falla del líder. A continuación se detallan los resultados de dichas pruebas:

\begin{itemize}
    \item Se simularon fallos en el líder en diferentes momentos, incluyendo durante la replicación de datos. En todos los casos, el sistema fue capaz de detectar la caída del líder y elegir un nuevo líder en cuestión de segundos mediante un proceso de votación entre los \textit{peers} activos en el sistema.
    
    \item Después de la elección de un nuevo líder, se intentó acceder a la base de datos, y se comprobó que los datos estaban al día, lo que demuestra que la replicación fue exitosa y que no hubo pérdida de información tras la caída del líder.
    
    \item Para garantizar la correcta operación del líder, se implementaron \textbf{heartbeats}, que el líder enviaba periódicamente al resto de los \textit{peers}. Estos \textit{heartbeats} permitían monitorear el estado del líder en todo momento. Por consola, se podía observar que el líder seguía funcionando mientras los \textit{heartbeats} llegaban a los \textit{followers}. Si se dejaban de recibir, se iniciaba una nueva votación para elegir un nuevo líder.
    
    \item Se registraron métricas sobre el tiempo que tarda el sistema en detectar la caída del líder y en realizar una nueva elección. El proceso de elección fue rápido y eficiente, con tiempos de respuesta muy bajos que garantizaron la disponibilidad continua del sistema.
    
    \item Se realizaron pruebas de carga para evaluar cómo el sistema maneja múltiples solicitudes de lectura y escritura al mismo tiempo. Los resultados mostraron que el sistema es capaz de manejar un alto volumen de tráfico sin degradar su rendimiento.
\end{itemize}

El líder envía latidos a sus followers. A continuación se muestra una imagen donde el líder envía los latidos, mostrando cómo se mantiene la comunicación activa con los \textit{followers}.

\begin{figure}[H]
    \centering
    \includegraphics[width=0.5\linewidth]{image1.png}
    \caption{El líder enviando latidos a sus seguidores.}
    \label{fig:latidos-leader}
\end{figure}

En la siguiente imagen, se observa a los followers recibiendo los latidos. Esto es crucial para que los followers sepan que el líder está activo y funcionando correctamente.

\begin{figure}[H]
    \centering
    \includegraphics[width=0.5\linewidth]{image2.png}
    \caption{Followers recibiendo latidos del líder.}
    \label{fig:latidos-followers}
\end{figure}

Si el líder se cae, el follower2 vota por el follower1 como nuevo líder. Esto se ilustra en la imagen a continuación, donde se muestra el proceso de votación.

\begin{figure}[H]
    \centering
    \includegraphics[width=0.5\linewidth]{image4.png}
    \caption{Follower2 votando por Follower1 como nuevo líder.}
    \label{fig:asignacion-lider}
\end{figure}

El follower1 detecta que el líder ha caído, por lo que inicia la votación para elegir un nuevo líder y vota por sí mismo. Esto se representa en la siguiente imagen, donde se muestra el proceso de votación en acción.

\begin{figure}[H]
    \centering
    \includegraphics[width=0.5\linewidth]{image3.png}
    \caption{Votación iniciada por el Follower1 para elegir un nuevo líder.}
    \label{fig:votacion-nuevo-lider}
\end{figure}

Si el viejo líder vuelve a integrarse al sistema, los followers recibirán nuevamente latidos de su parte. La imagen a continuación muestra cómo los followers vuelven a recibir mensajes del viejo líder, lo que indica que se ha recuperado correctamente.

\begin{figure}[H]
    \centering
    \includegraphics[width=0.5\linewidth]{image5.png}
    \caption{Followers recibiendo latidos del viejo líder tras su recuperación.}
    \label{fig:recuperacion-lider}
\end{figure}

\end{document}
