import { useReveal } from "../hooks/useReveal";

/**
 * NOTE FOR DEEPTI: the `github` and `demo` fields are left as `null`
 * on purpose — I don't have verified repo/deploy URLs for these projects.
 * Fill them in below and the buttons will activate automatically.
 * Projects marked `needsDetail: true` only have the feature list you
 * gave me — add a short real description before this goes live.
 */
const PROJECTS = [
  {
    title: "AI in Manufacturing",
    description:
      "An academic ML/AI project applying machine learning techniques to a manufacturing use case. Add a short description of the specific problem it solves (e.g. defect detection, predictive maintenance) and what you built.",
    tech: ["Python"],
    features: [],
    github: "https://github.com/sdeepti2136/ai-manufacturing",
    demo: null,
    needsDetail: true,
  },

  {
    title: "Fake Logo Detection",
    description:
      "A machine learning application that classifies uploaded logo images as genuine or counterfeit, with Grad-CAM visualizations to highlight the regions the model used to make its decision.",
    tech: ["Python", "TensorFlow / Keras", "React", "MySQL"],
    features: [
      "Image classification (genuine vs. counterfeit)",
      "Grad-CAM visual explanations",
      "JWT-based authentication",
      "React frontend for image upload & results",
    ],
    github: "https://github.com/sdeepti2136/fake-logo-detection",
    demo: null,
    needsDetail: false,
  },
];

export default function Projects() {
  const ref = useReveal();

  return (
    <section id="projects" className="section">
      <div className="container">
        <p className="eyebrow">05 projects</p>
        <h2 className="section-title">Projects</h2>
        <p className="section-sub">
          A selection of projects from my coursework and internship.
        </p>

        <div ref={ref} className="reveal projects__grid">
          {PROJECTS.map((project) => (
            <article key={project.title} className="project-card">
              <div className="project-card__head">
                <h3>{project.title}</h3>
                {project.needsDetail && (
                  <span className="project-card__flag mono">add details</span>
                )}
              </div>

              <p className="project-card__desc">{project.description}</p>

              {project.tech.length > 0 && (
                <div className="project-card__tech">
                  {project.tech.map((t) => (
                    <span key={t} className="project-card__tag">
                      {t}
                    </span>
                  ))}
                </div>
              )}

              {project.features.length > 0 && (
                <ul className="project-card__features">
                  {project.features.map((f) => (
                    <li key={f}>{f}</li>
                  ))}
                </ul>
              )}

              <div className="project-card__actions">
                {project.github ? (
                  <a
                    href={project.github}
                    target="_blank"
                    rel="noreferrer"
                    className="btn btn-outline btn-sm"
                  >
                    GitHub
                  </a>
                ) : (
                  <span className="btn btn-disabled btn-sm" aria-disabled="true">
                    GitHub (add link)
                  </span>
                )}

                {project.demo ? (
                  <a
                    href={project.demo}
                    target="_blank"
                    rel="noreferrer"
                    className="btn btn-primary btn-sm"
                  >
                    Live Demo
                  </a>
                ) : null}
              </div>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
