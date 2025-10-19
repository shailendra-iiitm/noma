
import torch
import torch.nn.functional as F

def multitask_loss(pos_logits, neg_logits, pos_rsum_pred, pos_alpha_pred,
                   pos_rsum_true, pos_alpha_true,
                   lambda_bce=1.0, lambda_rsum=0.5, lambda_alpha=0.5):
    """
    BCE on edges (pos=1, neg=0) + regression on Rsum and alpha for positives.
    """
    pos_labels = torch.ones_like(pos_logits)
    neg_labels = torch.zeros_like(neg_logits)
    logits = torch.cat([pos_logits, neg_logits], dim=0)
    labels = torch.cat([pos_labels, neg_labels], dim=0)

    loss_bce = F.binary_cross_entropy_with_logits(logits, labels)

    loss_rsum = F.l1_loss(pos_rsum_pred, pos_rsum_true)   # MAE is robust
    loss_alpha = F.l1_loss(pos_alpha_pred, pos_alpha_true)

    total = lambda_bce*loss_bce + lambda_rsum*loss_rsum + lambda_alpha*loss_alpha
    return total, {"bce": loss_bce.item(), "rsum": loss_rsum.item(), "alpha": loss_alpha.item()}
