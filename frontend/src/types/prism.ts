export interface AnalyzeRequest {
  product_name: string;
}

export interface ProductUnderstanding {
  product_name: string;
  category: string;
  target_users: string[];
  core_features: string[];
  value_prop: string;
  business_model: string;
  competitors: string[];
  confidence_score: number;
  confidence_level: string;
}

export interface JourneyStep {
  step: number;
  action: string;
  emotion: string;
  confusion_level: number;
  time_spent_seconds: number;
  confidence_level: string;
  evidence_type: string;
}

export interface PersonaSimulation {
  persona: string;
  journey_steps: JourneyStep[];
  friction_points: string[];
  drop_off_reason: string | null;
  satisfaction_score: number;
}

export interface SimulationOutput {
  personas: PersonaSimulation[];
}

export interface Problem {
  id: string;
  problem_type: string;
  description: string;
  severity: number;
  affected_persona: string;
}

export interface ProblemOutput {
  problems: Problem[];
}

export interface RootCause {
  problem_id: string;
  problem_type: string;
  root_cause: string;
  evidence_summary: string;
  confidence_level: string;
}

export interface RootCauseOutput {
  root_causes: RootCause[];
}

export interface Decision {
  priority_rank: number;
  action: string;
  root_cause: string;
  business_outcome: string;
  success_metric: string;
  rice_score: number;
}

export interface DecisionOutput {
  decisions: Decision[];
  product_health_score: number;
}

export interface PRISMAnalysis {
  product: ProductUnderstanding;
  simulation: SimulationOutput;
  problems: ProblemOutput;
  root_causes: RootCauseOutput;
  decisions: DecisionOutput;
  analyzed_at: string;
  pipeline_version: string;
}

export interface AnalyzeResponse {
  status: string;
  data: PRISMAnalysis;
  message: string;
}