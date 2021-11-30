from termcolor import cprint
from plots import plot_semilogy
import pandas as pd
from softmax import *
from copy import deepcopy
import pandas as pd
from termcolor import cprint

from plots import plot_semilogy
from softmax import *

DEBUG = True
seed = 1920


def test_grad_softmax(inputs, w, bias, one_hot_classes, iters=10, eps=0.1):
    d = np.random.rand(one_hot_classes.shape[0], inputs.shape[0])
    Z = w @ inputs + bias
    sm_wxb = softmax(Z)
    f0 = softmax_loss(sm_wxb, one_hot_classes)
    g0 = grad_softmax_loss_wrt_w(x=inputs, mat=sm_wxb, c=one_hot_classes)
    y0, y1 = np.zeros(iters), np.zeros(iters)
    df = pd.DataFrame(columns=["Error order 1", "Error order 2"])
    cprint("k\t error order 1 \t\t\t error order 2", 'green')
    for k in range(iters):
        epsk = eps * (0.5 ** k)
        A = (w + epsk * d) @ inputs + bias
        fk = softmax_loss(softmax(A), one_hot_classes)
        y0[k] = np.abs(fk - f0)
        y1[k] = np.abs(fk - f0 - epsk * np.sum(g0 * d))
        print(k, "\t", y0[k], "\t", y1[k])
        s = pd.Series([y0[k], y1[k]], index=df.columns.to_list())
        df = df.append(s, ignore_index=True)
    df.astype('string').to_csv('error_by_orders.csv')
    plot_semilogy([y0, y1])

def another_nn_grad_test(nn,x,y):
    Ygt = x
    Cgt = y

    weights = [nn.layers[layer].w for layer in nn.layers]
    w_shapes = [w.shape for w in weights]
    ds = [d / np.linalg.norm(d) for d in (np.random.default_rng().standard_normal(size=w) for w in w_shapes)]
    x = [np.random.default_rng().standard_normal(size=w) for w in w_shapes]

    def f(x):
        for layer, w in zip(nn.layers, x):
            nn.layers[layer].w = w
        out = nn.forward(Ygt)
        return softmax_loss(out, Cgt),out

    def grad(x,out):
        f(x)
        nn.backward(out,y)
        return np.concatenate(
            [np.ravel(nn.layers[layer].dw) for layer in nn.layers] , axis=0)

    eps_0 = 0.5
    eq_38 = []
    eq_39 = []
    fx,out = f(x)
    d_grad_x = np.concatenate([np.ravel(d) for d in ds]).T @ np.ravel(grad(x,out))
    for eps_i in np.geomspace(eps_0, eps_0 ** 5, 8):
        fx_eps_i_d,out1 = f([w + eps_i * d for w, d in zip(x, ds)])
        eq_38.append(np.abs(fx_eps_i_d - fx))
        eq_39.append(np.abs(fx_eps_i_d - fx - eps_i * d_grad_x))
    plot_semilogy([eq_38, eq_39])

def test_grad_softmax_nn(nn, x, y, iters=10, eps=0.1):
    layers_deepcopy = deepcopy(nn.layers)
    last_layer = list(nn.get_layers().values())[-1]
    pred = nn.forward(x)
    f0 = softmax_loss(pred, y)
    g0 = grad_softmax_loss_wrt_w(x=last_layer.x, mat=pred, c=y)
    nn.backward(pred, y)


    dws = dict()
    dbs = dict()
    gs = dict()
    gb = dict()
    layers_copy = {}
    for n, layer in nn.layers.items():
        layers_copy[n] = (deepcopy(layer.w), deepcopy(layer.b))
        dws[n] = np.random.rand(layer.w.shape[0], layer.w.shape[1])
        dws[n] = dws[n]/np.linalg.norm(dws[n])
        dbs[n] = np.random.rand(layer.b.shape[0], layer.b.shape[1])
        dbs[n] = dbs[n]/np.linalg.norm(dbs[n])
        gs[n] = layer.dw
        gb[n] = layer.db
        # dw = np.random.rand(y.shape[0], last_layer.x.shape[0])
    gd = sum([np.sum(g * dw) for g, dw in zip(gs.values(), dws.values())])
    gdb = sum([np.sum(g * dw) for g, dw in zip(gb.values(), dws.values())])
    y0, y1 = np.zeros(iters), np.zeros(iters)
    df = pd.DataFrame(columns=["Error order 1", "Error order 2"])
    cprint("k\t error order 1 \t\t\t error order 2", 'green')
    ggg=np.concatenate([np.ravel(nn.layers[layer].dw) for layer in nn.layers], axis=0)
    b = np.concatenate([np.ravel(dws[d]) for d in dws]).T
    a = np.ravel(ggg)

    giba = b @ a
    for k in range(iters):
        epsk = eps * (0.5 ** k)
        for n, layer in nn.layers.items():
            nn.layers[n].w = layers_deepcopy[n].w + epsk * dws[n]
            nn.layers[n].b = layers_deepcopy[n].b + epsk * dbs[n]

        pred_new = nn.forward(x)
        fk = softmax_loss(pred_new, y)
        y0[k] = np.abs(fk - f0)

        y1[k] = np.abs(fk - f0 - epsk * giba)
        ddd=dws['layer_4']
        #y1[k] = np.abs(fk - f0 - epsk*np.sum(g0 * dws['layer_4']))
        print(k, "\t", y0[k], "\t", y1[k])
        s = pd.Series([y0[k], y1[k]], index=df.columns.to_list())
        df = df.append(s, ignore_index=True)
    df.astype('string').to_csv('error_by_orders_nn.csv')
    plot_semilogy([y0, y1])


def run_test_grad_softmax():

    np.random.seed(seed=seed)

    n, m = 6, 3
    classes = 2

    X = np.random.randn(n, m)
    w = np.random.randn(classes, n)
    w = w / np.linalg.norm(w)

    print(f'l2 norm of x is {np.linalg.norm(X)}')
    print(f'l2 norm of w is {np.linalg.norm(w)}')
    y_vals = np.random.randint(low=0, high=classes, size=m)

    one_hot = np.eye(classes)[y_vals].T

    bias = np.random.rand(w.shape[0], 1)
    test_grad_softmax(X, w, bias, one_hot)



if __name__ == '__main__':
    run_test_grad_softmax()

