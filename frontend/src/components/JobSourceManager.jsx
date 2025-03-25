import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { toast } from '@/components/ui/use-toast';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Settings, Save, Upload, RefreshCw, AlertOctagon, CheckCircle } from 'lucide-react';
import api from '@/services/api';

const JobSourceManager = () => {
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchSources();
  }, []);

  const fetchSources = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.get('/job-search/sources');
      setSources(response.data.sources);
    } catch (err) {
      setError('Failed to load job sources: ' + (err.response?.data?.message || err.message));
    } finally {
      setLoading(false);
    }
  };

  const handleToggleSource = async (sourceName, enabled) => {
    try {
      const endpoint = enabled ? 'enable' : 'disable';
      const response = await api.post(`/job-search/sources/${sourceName}/${endpoint}`);
      
      // Update sources list with the new state
      setSources(sources.map(source => 
        source.name === sourceName ? { ...source, enabled } : source
      ));
      
      toast({
        title: 'Source updated',
        description: response.data.message,
        variant: 'success',
      });
    } catch (err) {
      toast({
        title: 'Failed to update source',
        description: err.response?.data?.message || err.message,
        variant: 'destructive',
      });
    }
  };

  const handleUpdatePriority = async (sourceName, priority) => {
    try {
      const response = await api.post(`/job-search/sources/${sourceName}/priority`, { priority });
      
      // Update sources list with the new priority
      setSources(sources.map(source => 
        source.name === sourceName ? { ...source, priority } : source
      ));
      
      toast({
        title: 'Priority updated',
        description: response.data.message,
        variant: 'success',
      });
    } catch (err) {
      toast({
        title: 'Failed to update priority',
        description: err.response?.data?.message || err.message,
        variant: 'destructive',
      });
    }
  };

  const handleUpdateWeight = async (sourceName, weight) => {
    try {
      const response = await api.post(`/job-search/sources/${sourceName}/weight`, { weight });
      
      // Update sources list with the new weight
      setSources(sources.map(source => 
        source.name === sourceName ? { ...source, weight } : source
      ));
      
      toast({
        title: 'Weight updated',
        description: response.data.message,
        variant: 'success',
      });
    } catch (err) {
      toast({
        title: 'Failed to update weight',
        description: err.response?.data?.message || err.message,
        variant: 'destructive',
      });
    }
  };

  const handleSaveConfig = async () => {
    try {
      setSaving(true);
      const response = await api.post('/job-search/sources/config/save');
      
      toast({
        title: 'Configuration saved',
        description: response.data.message,
        variant: 'success',
      });
    } catch (err) {
      toast({
        title: 'Failed to save configuration',
        description: err.response?.data?.message || err.message,
        variant: 'destructive',
      });
    } finally {
      setSaving(false);
    }
  };

  const handleLoadConfig = async () => {
    try {
      setLoading(true);
      const response = await api.post('/job-search/sources/config/load');
      
      if (response.data.status === 'success' && response.data.sources) {
        setSources(response.data.sources);
      }
      
      toast({
        title: 'Configuration loaded',
        description: response.data.message,
        variant: 'success',
      });
    } catch (err) {
      toast({
        title: 'Failed to load configuration',
        description: err.response?.data?.message || err.message,
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <RefreshCw className="h-8 w-8 animate-spin text-primary" />
        <span className="ml-2">Loading job sources...</span>
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive" className="my-4">
        <AlertOctagon className="h-4 w-4" />
        <AlertTitle>Error</AlertTitle>
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Job Source Registry</h2>
        <div className="flex gap-2">
          <Button onClick={fetchSources} variant="outline" size="sm">
            <RefreshCw className="mr-2 h-4 w-4" />
            Refresh
          </Button>
          <Button onClick={handleSaveConfig} disabled={saving} variant="outline" size="sm">
            <Save className="mr-2 h-4 w-4" />
            Save Config
          </Button>
          <Button onClick={handleLoadConfig} disabled={loading} variant="outline" size="sm">
            <Upload className="mr-2 h-4 w-4" />
            Load Config
          </Button>
        </div>
      </div>

      {sources.length === 0 ? (
        <Alert className="my-4">
          <CheckCircle className="h-4 w-4" />
          <AlertTitle>No sources</AlertTitle>
          <AlertDescription>No job sources are currently registered.</AlertDescription>
        </Alert>
      ) : (
        <ScrollArea className="h-[70vh]">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
            {sources.map((source) => (
              <Card key={source.name} className={source.enabled ? "border-primary" : "opacity-70"}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle className="capitalize">{source.name}</CardTitle>
                      <CardDescription>
                        Priority: {source.priority} | Weight: {source.weight}
                      </CardDescription>
                    </div>
                    <Switch
                      checked={source.enabled}
                      onCheckedChange={(checked) => handleToggleSource(source.name, checked)}
                    />
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <Label htmlFor={`priority-${source.name}`}>Priority</Label>
                      <span className="text-sm">{source.priority}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Slider
                        id={`priority-${source.name}`}
                        defaultValue={[source.priority]}
                        min={1}
                        max={20}
                        step={1}
                        onValueCommit={(value) => handleUpdatePriority(source.name, value[0])}
                      />
                      <Input 
                        type="number" 
                        min={1}
                        max={20}
                        value={source.priority}
                        onChange={(e) => handleUpdatePriority(source.name, parseInt(e.target.value) || 1)}
                        className="w-16"
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <Label htmlFor={`weight-${source.name}`}>Weight</Label>
                      <span className="text-sm">{source.weight}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Slider
                        id={`weight-${source.name}`}
                        defaultValue={[source.weight]}
                        min={1}
                        max={20}
                        step={1}
                        onValueCommit={(value) => handleUpdateWeight(source.name, value[0])}
                      />
                      <Input 
                        type="number" 
                        min={1}
                        max={20}
                        value={source.weight}
                        onChange={(e) => handleUpdateWeight(source.name, parseInt(e.target.value) || 1)}
                        className="w-16"
                      />
                    </div>
                  </div>

                  {source.config && Object.keys(source.config).length > 0 && (
                    <div className="space-y-2">
                      <Label>Configuration</Label>
                      <pre className="whitespace-pre-wrap rounded bg-muted p-2 text-xs">
                        {JSON.stringify(source.config, null, 2)}
                      </pre>
                    </div>
                  )}
                </CardContent>
                <CardFooter className="flex justify-end">
                  <Button variant="outline" size="sm">
                    <Settings className="mr-2 h-4 w-4" />
                    Configure
                  </Button>
                </CardFooter>
              </Card>
            ))}
          </div>
        </ScrollArea>
      )}
    </div>
  );
};

export default JobSourceManager;
