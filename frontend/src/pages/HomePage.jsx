import { ArrowRight, Briefcase, Rss, Settings } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

function NavCard({ icon: Icon, title, description, onClick }) {
  return (
    <button
      onClick={onClick}
      className="group relative flex flex-col items-start p-8 bg-white border border-gray-100 rounded-2xl hover:border-gray-200 hover:shadow-card transition-all duration-300 w-full text-left overflow-hidden"
    >
      <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent to-transparent group-hover:from-gray-200 group-hover:to-gray-300 transition-all duration-500"></div>

      <div className="p-4 mb-6 bg-gray-50 rounded-xl group-hover:bg-charcoal group-hover:text-white text-charcoal transition-colors duration-300">
        <Icon className="w-7 h-7" />
      </div>

      <h2 className="text-2xl font-semibold text-charcoal-dark mb-3 tracking-tight">{title}</h2>
      <p className="text-gray-500 leading-relaxed mb-8">{description}</p>

      <div className="mt-auto flex items-center text-sm font-medium text-charcoal-light group-hover:text-charcoal-dark transition-colors">
        <span>Get started</span>
        <ArrowRight className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />
      </div>
    </button>
  )
}

export function HomePage() {
  const navigate = useNavigate()

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-[#FAFAFA] p-6 font-sans relative overflow-hidden">
      <div className="absolute top-[-10%] left-[-10%] w-96 h-96 bg-gray-100 rounded-full blur-3xl opacity-50 pointer-events-none"></div>
      <div className="absolute bottom-[-10%] right-[-10%] w-96 h-96 bg-gray-100 rounded-full blur-3xl opacity-50 pointer-events-none"></div>

      <div className="z-10 text-center mb-16 max-w-2xl">
        <h1 className="text-4xl md:text-5xl font-bold text-charcoal-dark mb-6 tracking-tight">
          Welcome to{' '}
          <span className="text-charcoal relative inline-block">
            Resume Tracker Pro
            <span className="absolute bottom-1 left-0 w-full h-3 bg-gray-200 -z-10 transform -rotate-1"></span>
          </span>
        </h1>
        <p className="text-lg text-gray-500 font-light">
          Your AI-powered career assistant. Streamline your job hunt, discover tailored roles, and manage your applications seamlessly.
        </p>
      </div>

      <div className="z-10 grid grid-cols-1 md:grid-cols-3 gap-6 w-full max-w-6xl">
        <NavCard
          icon={Briefcase}
          title="Job Tracker"
          description="Keep all your applications, interviews, and offers organized in a centralized, intelligent dashboard."
          onClick={() => navigate('/tracker')}
        />
        <NavCard
          icon={Rss}
          title="Daily Role Feed"
          description="Discover fresh, curated opportunities that match your specific profile, updated daily."
          onClick={() => navigate('/roles')}
        />
        <NavCard
          icon={Settings}
          title="Settings & Config"
          description="Customize your personal profile, fine-tune ranking engine rules, and manage data sources."
          onClick={() => navigate('/config')}
        />
      </div>
    </div>
  )
}

