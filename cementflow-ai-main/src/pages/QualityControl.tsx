import { useState, useEffect, useRef } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceArea
} from "recharts";
import {
  Shield,
  Bot,
  FlaskConical,
  Zap,
  AlertTriangle,
  CheckCircle2,
  Settings,
  Loader2
} from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";

interface QCData {
  timestamp: string;
  LSF_est: number;
  Blaine_est: number;
  fCaO_est: number;
}

interface Plan {
  issue: string;
  kpi_impact: any;
  actions: { knob: string; delta_pct: number; reason: string }[];
  notes?: string;
}

interface SimulationResult {
  simulated_after: {
    LSF_est: number;
    Blaine_est: number;
    fCaO_est: number;
  };
}

const QualityControl = () => {
  const [qcData, setQcData] = useState<QCData[]>([]);
  const [proposedPlan, setProposedPlan] = useState<Plan | null>(null);
  const [simulationResults, setSimulationResults] = useState<SimulationResult | null>(null);
  const [isLoading, setIsLoading] = useState<string | boolean>(false);
  const [disturbanceValue, setDisturbanceValue] = useState("SiO2_in_high");
  const [disturbanceMagnitude, setDisturbanceMagnitude] = useState(5);
  const { toast } = useToast();
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const fetchChartData = async () => {
    try {
      const response = await fetch("http://localhost:8002/state/series?last_seconds=600");
      if (response.ok) {
        const data = await response.json();
        const formattedData = data.map((d: any) => {
          if (!d.timestamp) {
            return { ...d, timestamp: "Unknown Time" };
          }
          const date = new Date(d.timestamp);
          return {
            ...d,
            timestamp: !isNaN(date.getTime()) ? date.toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' }) : "Invalid Time",
          }
        });
        setQcData(formattedData);
      }
    } catch (error) {
      console.error("Failed to fetch chart data", error);
    }
  };

  useEffect(() => {
    fetchChartData();
    intervalRef.current = setInterval(fetchChartData, 5000);
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, []);

  const proposePlan = async () => {
    setIsLoading("propose");
    setProposedPlan(null);
    setSimulationResults(null);
    toast({ title: "AI Analysis Started", description: "Generating corrective plan..." });

    try {
      const response = await fetch("http://localhost:8002/plan/propose?force=true", { method: "POST" });
      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || "Failed to propose plan");
      }
      const plan = await response.json();
      setProposedPlan(plan);
      toast({ title: "Plan Generated", description: "AI corrective plan is ready for review" });
    } catch (error: any) {
      toast({ title: "Plan Generation Failed", description: error.message, variant: "destructive" });
    } finally {
      setIsLoading(false);
    }
  };

  const simulatePlan = async () => {
    if (!proposedPlan) return;
    setIsLoading("simulate");
    toast({ title: "Simulation Started", description: "Testing plan effectiveness..." });

    try {
      const response = await fetch("http://localhost:8002/plan/simulate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(proposedPlan),
      });
      if (!response.ok) throw new Error("Failed to simulate plan");
      const results = await response.json();
      setSimulationResults(results);
      toast({ title: "Simulation Complete", description: "Plan effectiveness confirmed" });
    } catch (error: any) {
      toast({ title: "Simulation Failed", description: error.message, variant: "destructive" });
    } finally {
      setIsLoading(false);
    }
  };

  const applyPlan = async () => {
    if (!proposedPlan) return;
    setIsLoading("apply");
    toast({ title: "Applying Plan", description: "Implementing corrective actions..." });

    try {
      const response = await fetch("http://localhost:8002/plan/apply", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(proposedPlan),
      });
      if (!response.ok) throw new Error("Failed to apply plan");
      toast({ title: "Plan Applied", description: "Corrective actions have been implemented" });
      setTimeout(() => {
        setProposedPlan(null);
        setSimulationResults(null);
      }, 1000);
    } catch (error: any) {
      toast({ title: "Failed to Apply Plan", description: error.message, variant: "destructive" });
    } finally {
      setIsLoading(false);
    }
  };

  const injectDisturbance = async () => {
    setIsLoading("disturb");
    toast({ title: "Injecting Disturbance", description: `Applying ${disturbanceValue}` });

    try {
      const response = await fetch("http://localhost:8002/disturb", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ type: disturbanceValue, magnitude: disturbanceMagnitude, duration_s: 60 }),
      });
      if (!response.ok) throw new Error("Failed to inject disturbance");
      toast({ title: "Disturbance Injected", description: "Process disturbance is now active" });
    } catch (error: any) {
      toast({ title: "Failed to Inject Disturbance", description: error.message, variant: "destructive" });
    } finally {
      setIsLoading(false);
    }
  };
  
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-card border border-border p-3 rounded-lg shadow-lg">
          <p className="text-sm font-medium text-foreground mb-2">{`Time: ${label}`}</p>
          {payload.map((entry: any, index: number) => (
            <p key={index} className="text-sm" style={{ color: entry.color }}>
              {`${entry.name}: ${entry.value.toFixed(entry.name === 'Blaine_est' ? 0 : 2)}`}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };


  return (
    <div className="min-h-screen bg-background p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-foreground mb-2">Proactive Quality Control Center</h1>
        <p className="text-muted-foreground">Real-time quality monitoring with AI-powered corrective planning</p>
      </div>

      <Card className="mb-6 bg-card/50 backdrop-blur border-border shadow-card-elevated">
        <CardHeader><CardTitle className="text-xl font-semibold">Live Quality Parameters</CardTitle></CardHeader>
        <CardContent>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={qcData}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--chart-grid))" />
                <XAxis dataKey="timestamp" stroke="hsl(var(--muted-foreground))" fontSize={12} />
                <YAxis yAxisId="left" domain={[0.8, 1.1]} stroke="hsl(var(--muted-foreground))" fontSize={12} />
                <YAxis yAxisId="right" orientation="right" domain={[3600, 4200]} stroke="hsl(var(--muted-foreground))" fontSize={12} />
                <Tooltip content={<CustomTooltip />} />
                <ReferenceArea yAxisId="left" y1={0.92} y2={0.98} fill="hsl(var(--chart-success))" fillOpacity={0.1} label={{ value: "LSF Target", position: "insideTopLeft", fill: "hsl(var(--chart-success))" }} />
                <Line yAxisId="left" type="monotone" dataKey="LSF_est" name="LSF" stroke="hsl(var(--chart-primary))" strokeWidth={2} dot={false} />
                <Line yAxisId="right" type="monotone" dataKey="Blaine_est" name="Blaine" stroke="hsl(var(--chart-secondary))" strokeWidth={2} dot={false} />
                <Line yAxisId="left" type="monotone" dataKey="fCaO_est" name="fCaO" stroke="hsl(var(--chart-danger))" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <Card className="bg-card/50 backdrop-blur border-border shadow-card-elevated">
          <CardHeader><CardTitle className="text-xl font-semibold">Issue Detector & Proposer</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <Button onClick={proposePlan} disabled={!!isLoading} className="w-full bg-gradient-primary hover:opacity-90 text-primary-foreground">
              {isLoading === 'propose' ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Bot className="mr-2 h-4 w-4" />}
              {isLoading === 'propose' ? 'Analyzing...' : 'Propose Corrective Plan'}
            </Button>
            {proposedPlan && (
              <div className="p-4 bg-primary/10 rounded-lg border border-primary/20">
                <div className="flex items-center gap-2 mb-3"><Bot className="h-5 w-5 text-primary" /><span className="font-medium text-primary">AI Generated Plan</span></div>
                <div className="space-y-3">
                  <div>
                    <h4 className="text-sm font-medium text-foreground mb-2">Issue Detected:</h4>
                    <p className="text-sm text-muted-foreground">{proposedPlan.issue}</p>
                  </div>
                  <div>
                    <h4 className="text-sm font-medium text-foreground mb-2">Proposed Actions:</h4>
                    <div className="space-y-1">
                      {proposedPlan.actions.map((action, index) => (
                        <p key={index} className="text-sm text-foreground">• {action.reason}</p>
                      ))}
                    </div>
                  </div>
                  {proposedPlan.notes && (
                    <div>
                      <h4 className="text-sm font-medium text-foreground mb-2">Notes:</h4>
                      <p className="text-sm text-muted-foreground whitespace-pre-wrap">{proposedPlan.notes}</p>
                    </div>
                  )}
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="bg-card/50 backdrop-blur border-border shadow-card-elevated">
          <CardHeader><CardTitle className="text-xl font-semibold">Plan Simulation & Application</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <Button onClick={simulatePlan} disabled={!!isLoading || !proposedPlan} className="w-full bg-gradient-secondary hover:opacity-90 text-secondary-foreground">
              {isLoading === 'simulate' ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <FlaskConical className="mr-2 h-4 w-4" />}
              {isLoading === 'simulate' ? 'Simulating...' : 'Simulate Plan'}
            </Button>
            {simulationResults && (
              <div className="p-4 bg-secondary/10 rounded-lg border border-secondary/20">
                <div className="flex items-center gap-2 mb-3"><FlaskConical className="h-5 w-5 text-secondary" /><span className="font-medium text-secondary">Simulation Results</span></div>
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div>
                    <h4 className="text-sm font-medium text-foreground mb-2">Before</h4>
                    <div className="space-y-1 text-sm">
                      <p>LSF: {qcData.length > 0 ? qcData[qcData.length - 1].LSF_est.toFixed(2) : 'N/A'}</p>
                      <p>Blaine: {qcData.length > 0 ? Math.round(qcData[qcData.length - 1].Blaine_est) : 'N/A'}</p>
                      <p>Free CaO: {qcData.length > 0 ? qcData[qcData.length - 1].fCaO_est.toFixed(1) : 'N/A'}%</p>
                    </div>
                  </div>
                  <div>
                    <h4 className="text-sm font-medium text-foreground mb-2">After</h4>
                    <div className="space-y-1 text-sm text-success">
                      <p>LSF: {simulationResults.simulated_after.LSF_est.toFixed(2)}</p>
                      <p>Blaine: {Math.round(simulationResults.simulated_after.Blaine_est)}</p>
                      <p>Free CaO: {simulationResults.simulated_after.fCaO_est.toFixed(1)}%</p>
                    </div>
                  </div>
                </div>
              </div>
            )}
            <Dialog>
              <DialogTrigger asChild>
                <Button disabled={!!isLoading || !simulationResults} className="w-full bg-gradient-danger hover:opacity-90 text-danger-foreground">
                  <Zap className="mr-2 h-4 w-4" /> Apply Plan to Plant
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader><DialogTitle>Confirm Plan Application</DialogTitle><DialogDescription>Are you sure you want to apply the corrective plan to the plant?</DialogDescription></DialogHeader>
                <DialogFooter>
                  <Button variant="outline">Cancel</Button>
                  <Button onClick={applyPlan} className="bg-gradient-danger hover:opacity-90">Apply Plan</Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </CardContent>
        </Card>
      </div>

      <Card className="bg-card/50 backdrop-blur border-border shadow-card-elevated">
        <CardHeader><CardTitle className="text-lg font-semibold">Disturbance Panel (Demo)</CardTitle></CardHeader>
        <CardContent>
          <div className="flex items-end gap-4">
            <div className="flex-1">
              <Label htmlFor="disturbance" className="text-sm font-medium">Inject Process Disturbance</Label>
              <Input id="disturbance" value={disturbanceValue} onChange={(e) => setDisturbanceValue(e.target.value)} className="mt-2" />
            </div>
            <div className="w-1/4">
              <Label htmlFor="magnitude" className="text-sm font-medium">Magnitude</Label>
              <Input id="magnitude" type="number" value={disturbanceMagnitude} onChange={(e) => setDisturbanceMagnitude(Number(e.target.value))} className="mt-2" />
            </div>
            <Button onClick={injectDisturbance} disabled={!!isLoading} variant="outline" className="border-warning text-warning hover:bg-warning/10">
              {isLoading === 'disturb' ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Settings className="mr-2 h-4 w-4" />}
              Inject
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default QualityControl;
