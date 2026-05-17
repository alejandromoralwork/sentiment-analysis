1.1. Task 1: Sentiment analysis from news articles
The marketing department has asked you to analyze how your company is perceived in the market. Therefore,
they want you to develop an application that is able to identify the sentiment of recent news about the company.
To make this project feasible, we will limit ourselves to what is available within the given course and/ortimeframe.
You can decide by yourself, if you want to rate the news articles according to their valence (i.e., being positive,
neutral, or negative) or use categorical emotions such as joy, anger, or fear. It is up to you to choose which technologies (frameworks, programming languages, etc.) you use for the components and the communication between the components.
It is mandatory to be able to identify at least three different emotional states/levels of valence.
Task: Implementation of a sentiment analysis tool that is able to crawl the news for a given keyword (i.e., company name) and detect the sentiment of recent news articles about the company.
Implement the analysis tool in the following 3 phases:
1.1.1. Conception phase
This phase represents the most important part of the design process. Anything that is overlooked or forgotten in
this phase has a negative effect on the implementation later and will lead, in the worst case, to useless results.
The first step is to create a written concept, to describe everything that belongs to the sentiment analysis application. At least 1 diagram (e.g., using unified modeling language – UML) will be created and inserted into the
written concept to show the interaction of the components and the process. This step is perhaps the most important of the entire design process. It is crucial to take/plan enough time for this phase BEFORE the next steps
can be taken. It is therefore essential to follow the sequence of the respective steps carefully.
It is important to not only perform the sentiment analysis on the news articles but also to be able to validate the
quality of the classification. The written concept must explain how the process of classification and validation
works and why the structure and the process of the application have been conceptualized in the particular manner.
Think about which framework and which tools you can use to implement each component and the communication between the components. Then name the planned frameworks and tools and explain your decisions.
Seite 3 von 12
PRÜFUNGSAMT
IU.DE
A conceptual text (1 DIN A4 page PDF-file) has to be prepared for the submission, explaining these analyses and
considerations, together with the diagram showing the interaction of the components and the process. The text
field inside the PebblePad template can be left empty.
Throughout the process, online tutorials are offered, and they provide an opportunity to talk, share ideas and/or
drafts, and obtain feedback. In the online tutorials, exemplary work can be discussed with the tutor. Here, everyone has the opportunity to get involved and learn from each other's feedback. It is recommended to make use
of these channels to avoid errors and to make improvements. You should only submit work after making use
of the above-mentioned tutorial and informative media. This will be followed by feedback from the tutor and the
work on the second phase can begin.


1.1.2. Development phase/reflection phase
In this phase, the sentiment analysis tool is implemented based on the concept from the conception phase with
the help of the selected frameworks and tools. This is where the actual work of implementation begins:
• The frameworks and tools are set up.
• The components outlined in the diagram are implemented.
• The code is commented.
• The training data for the sentiment analysis is collected.
• The NLP models are trained.
• Iterative optimization of the system.

An explanation of the procedure is submitted as a composite presentation PDF with approx. 10 slides. The file
should contain visual elements that facilitate comprehension. It needs to be structured and also include hyperlinks to the frameworks which have been used. Furthermore, the procedure should be described briefly. 


1.1.3. Finalization phase
In the finalization phase, the goal is to optimize the sentiment analysis tool after having received feedback from
the tutor and to complete the task. Certain elements may have to be improved or changed again.
Additionally, an abstract is desired which describes the solution of the task in terms of content and concept and
which presents a short break-down (making of) about the technical approach in a clear and informative way. The
finished product (i.e., scripts with installation manual and documentation included) is submitted, together with
the abstract, and the results from phases 1 and 2. In addition, a zip folder (containing all used files) created specifically for this course should be included in the PebblePad template.
 
For workplace-style delivery to a non-technical department (e.g., marketing), include the following in the final
package:
\begin{itemize}
	\item An executable wrapper (or clear build instructions) so the tool can run without a developer environment.
	\item A `UserGuide.md` that explains how to run the executable and interpret reports.
	\item A `DeveloperGuide.md` that documents architecture, reproducibility steps and packaging notes (model ids, pinned requirements).
	\item A `.env.example` and instructions on where to store API keys (do not include secrets in the submission).
\end{itemize}
In the “Finalization phase”, the online tutorials and other channels also provide the opportunity to obtain sufficient feedback, tips, and hints before the finished product is finally handed in. It is recommended to use these
channels to avoid errors and to make improvements. The finished product is submitted with the results from
Phase 1 and Phase 2 and together with the materials mentioned above. Following the submission of the third
portfolio page, the tutor submits the final feedback which includes evaluation and scoring within six weeks.