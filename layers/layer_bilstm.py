import torch
import torch.nn as nn

from layers.layer_birnn_base import LayerBiRNNBase

class LayerBiLSTM(LayerBiRNNBase):
    def __init__(self, input_dim, hidden_dim, gpu):
        super(LayerBiLSTM, self).__init__(input_dim, hidden_dim, gpu)
        self.num_layers = 1
        self.num_directions = 2
        rnn = nn.LSTM(input_size=input_dim,
                      hidden_size=hidden_dim,
                      num_layers=1,
                      batch_first=True,
                      bidirectional=True)
        nn.init.xavier_uniform_(rnn.weight_hh_l0)
        nn.init.xavier_uniform_(rnn.weight_hh_l0_reverse)
        nn.init.xavier_uniform_(rnn.weight_ih_l0)
        nn.init.xavier_uniform_(rnn.weight_ih_l0_reverse)
        rnn.bias_hh_l0.data.fill_(0)
        rnn.bias_hh_l0_reverse.data.fill_(0)
        rnn.bias_ih_l0.data.fill_(0)
        rnn.bias_ih_l0_reverse.data.fill_(0)
        # Init forget gates to 1
        for names in rnn._all_weights:
            for name in filter(lambda n: 'bias' in n, names):
                bias = getattr(rnn, name)
                n = bias.size(0)
                start, end = n // 4, n // 2
                bias.data[start:end].fill_(1.)
        self.rnn = rnn

    def forward(self, input_tensor, mask_tensor): #input_tensor shape: batch_size x max_seq_len x dim
        batch_size, max_seq_len, _ = input_tensor.shape
        h0 = self.tensor_ensure_gpu(torch.zeros(self.num_layers * self.num_directions, batch_size, self.hidden_dim))
        c0 = self.tensor_ensure_gpu(torch.zeros(self.num_layers * self.num_directions, batch_size, self.hidden_dim))
        output, _ = self.rnn(input_tensor, (h0, c0))
        return self.apply_mask(output)  # shape: batch_size x max_seq_len x hidden_dim*2

    def is_cuda(self):
        return self.rnn.weight_hh_l0.is_cuda

    '''
    def __forward_old(self, input_tensor): #input_tensor shape: batch_size x max_seq_len x dim
        batch_size, max_seq_len, _ = input_tensor.shape
        # Init rnn's states by zeros
        rnn_forward_h = self.make_gpu(torch.zeros(batch_size, self.hidden_dim))
        rnn_backward_h = self.make_gpu(torch.zeros(batch_size, self.hidden_dim))
        rnn_forward_c = self.make_gpu(torch.zeros(batch_size, self.hidden_dim))
        rnn_backward_c = self.make_gpu(torch.zeros(batch_size, self.hidden_dim))
        # Forward pass in both directions
        output = self.make_gpu(torch.zeros(batch_size, max_seq_len, self.hidden_dim * 2))
        for l in range(max_seq_len):
            n = max_seq_len - l - 1
            rnn_forward_h, rnn_forward_c = self.rnn_forward_layer(input_tensor[:, l, :], (rnn_forward_h, rnn_forward_c))
            rnn_backward_h, rnn_backward_c = self.rnn_backward_layer(input_tensor[:, n, :], (rnn_backward_h, rnn_backward_c))
            output[:, l, :self.hidden_dim] = rnn_forward_h
            output[:, n, self.hidden_dim:] = rnn_backward_h
        return output
    '''