# Knowledge Graph UI Enhancement Plan

## Current State Assessment
- **Canvas-based force-directed graph** using physics simulation
- **Basic node detail panel** showing raw metadata on right slide-over
- **Limited interactivity** - only click to select node
- **No data enrichment** - just displays what backend sends
- **Basic styling** - minimal visual hierarchy

## Goals
1. ✅ Make the node detail panel more informative and visually appealing
2. ✅ Add interactive features (hover effects, relationship exploration)
3. ✅ Implement dynamic data fetching for enriched node information
4. ✅ Improve visual hierarchy and UI/UX
5. ✅ Add search/filter functionality
6. ✅ Show relationship types and connected nodes clearly

## Implementation Phases

### Phase 1: Enhanced Node Detail Panel (Core)
- **Location**: Right slide-over panel
- **Improvements**:
  - Rich node header with icon and type badge
  - Relationship section showing connected nodes
  - Categorized metadata display (Properties, Relationships, Intelligence)
  - Evidence/findings associated with node
  - Visual indicators for node importance/severity
  - Related nodes quick links
  - Copy-to-clipboard buttons for important values

### Phase 2: Visual & Interactive Improvements
- **Hover Effects**:
  - Highlight hovered node and connected nodes (1-2 hops)
  - Show node tooltip on hover
  - Highlight incoming/outgoing edges with different colors
  
- **Node Styling**:
  - Enhanced color coding by node type
  - Size variation by importance/connections
  - Glow effect for selected node
  - Animation on selection

- **Search & Filter**:
  - Search box in top panel
  - Filter by node type
  - Filter by severity/importance

### Phase 3: Data Enrichment
- **Backend API Calls** to fetch:
  - Node-specific threat intelligence (for IOCs)
  - Related findings and evidence
  - Connection context and relationship explanations
  - Historical data (if available)

- **Smart Data Display**:
  - Show IOC reputation scores
  - Display related findings for each node
  - Show evidence that connects to this node
  - Timeline of discovery/detection

### Phase 4: Relationship Visualization
- **Show Relationship Types**:
  - Different edge colors/styles for different relationship types
  - Edge labels for critical relationships
  - Relationship count badges

- **Expand Connected Nodes**:
  - Show connected nodes in sidebar
  - Navigate to connected nodes easily
  - Show relationship type between nodes

## Technical Implementation Details

### Modified Files
1. **KnowledgeGraph.tsx** - Main graph component
   - Add state for hover, search, filter
   - Enhance node detail panel with new sections
   - Add tooltip rendering
   - Add search/filter UI

2. **store.ts** - Zustand store
   - Add new actions for fetching node details
   - Cache fetched data to avoid repeated requests
   - Add node enrichment data structure

3. **New Component**: `NodeDetailPanel.tsx`
   - Extract node detail logic into separate component
   - Organize into sections (Header, Relationships, Metadata, Evidence)
   - Add loading states and error handling

4. **Backend API** (new endpoints needed)
   - `GET /api/audit/:auditId/graph/node/:nodeId` - Get enriched node data
   - `GET /api/audit/:auditId/graph/node/:nodeId/relationships` - Get connected nodes
   - `GET /api/audit/:auditId/graph/node/:nodeId/evidence` - Get evidence connecting to node

## Data Structure Changes

### Node Enrichment Data
```typescript
interface EnrichedNode {
  id: string;
  label: string;
  type: string;
  severity?: 'critical' | 'high' | 'medium' | 'low';
  confidence?: number;
  nodeCount: number;  // Number of unique connections
  incomingEdges: Array<{nodeId: string; nodeLabel: string; type: string}>;
  outgoingEdges: Array<{nodeId: string; nodeLabel: string; type: string}>;
  evidence: Array<{id: string; finding: string; severity: string}>;
  intelligence?: {
    reputation?: number;
    firstSeen?: string;
    lastSeen?: string;
    tags?: string[];
  };
  raw: Record<string, any>;
}
```

## UI/UX Improvements

### Node Detail Panel Sections
1. **HEADER** - Node name, type badge, severity indicator
2. **RELATIONSHIPS** - Connected nodes (in/out), edge types
3. **EVIDENCE** - Findings and evidence connected to this node
4. **PROPERTIES** - Key-value metadata
5. **INTELLIGENCE** - Threat intel (if available)
6. **CONNECTIONS** - Visual relationship count

### Search/Filter Bar
- Global search across node names/labels
- Type filter (IOC, OSINT, Entity, etc.)
- Severity/importance filter
- Show matching count

### Visual Improvements
- Better color scheme for different node types
- Size nodes by connection count or importance
- Enhanced glow effects
- Better label rendering and positioning
- Smooth transitions and animations

## Error Handling & Edge Cases
- Handle nodes with no additional data gracefully
- Show loading states when fetching node details
- Cache API responses to avoid repeated requests
- Handle API errors with user-friendly messages
- Support very large graphs (1000+ nodes) efficiently

## Testing Points
- ✅ Click on various node types
- ✅ Verify all node details load correctly
- ✅ Test search/filter functionality
- ✅ Verify hover effects work
- ✅ Check performance with large graphs
- ✅ Verify no new rendering errors

## Success Criteria
1. Node detail panel shows enriched data with clear sections
2. Hover effects highlight connected nodes
3. Search/filter works smoothly
4. No rendering performance degradation
5. All interactive features work without errors
6. UI looks professional and matches terminal aesthetic
