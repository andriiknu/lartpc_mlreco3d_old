# Using trained UResNet for feature extractor
import torch
from mlreco.models.uresnet_lonely import UResNet

class ClustUResNetNodeEncoder(torch.nn.Module):
    """
    Uses a UResNet to produce node features for cluster GNN

    """
    def __init__(self, model_config):
        super(ClustUResNetNodeEncoder, self).__init__()

        # Initialize the UResNet
        self.encoder = UResNet(model_config)

        # flag for whether to freeze, default True
        self._freeze = model_config.get("freeze_uresnet", True)
        if self._freeze:
            for param in self.encoder:
                param.requires_grad = False


    def forward(self, data, clusts):
        # Use cluster ID as a batch ID, pass through CNN
        device = data.device
        cnn_data = torch.empty((0, 5), device=device, dtype=torch.float)
        for i, c in enumerate(clusts):
            cnn_data = torch.cat((cnn_data, data[c, :5].float()))
            cnn_data[-len(c):, 3] = i * torch.ones(len(c)).to(device)

        out = self.encoder(cnn_data)['ppn_feature_dec']
        print("out = " +str(out))
        return self.encoder(cnn_data)['ppn_feature_dec'][0][0]


class ClustUResNetEdgeEncoder(torch.nn.Module):
    """
    Uses a UResNet to produce node features for cluster GNN

    """
    def __init__(self, model_config):
        super(ClustUResNetEdgeEncoder, self).__init__()

        # Initialize the UResNet
        self.encoder = UResNet(model_config)

        # flag for whether to freeze, default True
        self._freeze = model_config.get("freeze_uresnet", True)
        if self._freeze:
            for param in self.encoder:
                param.requires_grad = False

    def forward(self, data, clusts, edge_index):

        # Check if the graph is undirected, select the relevant part of the edge index
        half_idx = int(edge_index.shape[1]/2)
        undirected = (not edge_index.shape[1]%2 and [edge_index[1,0], edge_index[0,0]] == edge_index[:,half_idx].tolist())
        if undirected: edge_index = edge_index[:,:half_idx]

        # Use edge ID as a batch ID, pass through CNN
        device = data.device
        cnn_data = torch.empty((0, 5), device=device, dtype=torch.float)
        for i, e in enumerate(edge_index.T):
            ci, cj = clusts[e[0]], clusts[e[1]]
            cnn_data = torch.cat((cnn_data, data[ci,:5].float()))
            cnn_data = torch.cat((cnn_data, data[cj,:5].float()))
            cnn_data[-len(ci)-len(cj):,3] = i*torch.ones(len(ci)+len(cj)).to(device)

        feats = self.encoder(cnn_data)['ppn_feature_dec'][0][0]

        # If the graph is undirected, duplicate features
        if undirected:
            feats = torch.cat([feats, feats])

        return feats


