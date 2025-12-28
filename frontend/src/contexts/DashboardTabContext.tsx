import React, { createContext, useContext, useState } from 'react'

interface DashboardTabContextType {
  tabValue: number
  setTabValue: (value: number) => void
}

const DashboardTabContext = createContext<DashboardTabContextType | undefined>(undefined)

export const DashboardTabProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [tabValue, setTabValue] = useState(0)

  return (
    <DashboardTabContext.Provider value={{ tabValue, setTabValue }}>
      {children}
    </DashboardTabContext.Provider>
  )
}

export const useDashboardTab = () => {
  const context = useContext(DashboardTabContext)
  if (!context) {
    throw new Error('useDashboardTab must be used within DashboardTabProvider')
  }
  return context
}
