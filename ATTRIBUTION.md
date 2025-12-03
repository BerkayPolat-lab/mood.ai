# Attribution

This document provides detailed attributions for all sources, models, datasets, libraries, and AI-generated content used in the mood.ai project.

---

## Machine Learning Models

### YAMNet
- **Model**: YAMNet (Yet Another Mobile Network)
- **Source**: Google Research / TensorFlow Hub
- **License**: Apache License 2.0
- **URL**: https://tfhub.dev/google/yamnet/1
- **Purpose**: Sound classification (521 audio event classes)
- **Citation**: 
  - Plakal, M., & Ellis, D. P. W. (2020). YAMNet: Yet Another Mobile Network. In *ICASSP 2020 - 2020 IEEE International Conference on Acoustics, Speech and Signal Processing (ICASSP)* (pp. 6989-6993). IEEE.
- **Class Names Source**: 
  - TensorFlow Models Repository
  - URL: https://raw.githubusercontent.com/tensorflow/models/master/research/audioset/yamnet/yamnet_class_map.csv
  - License: Apache License 2.0

### HuBERT Base Model
- **Model**: `superb/hubert-base-superb-er`
- **Source**: SUPERB (Speech processing Universal PERformance Benchmark) / Hugging Face
- **License**: Apache License 2.0
- **URL**: https://huggingface.co/superb/hubert-base-superb-er
- **Purpose**: Pre-trained HuBERT model for emotion recognition
- **Baseline Performance**:
  - s3prl framework: 0.6492 (64.92%)
  - transformers framework: 0.6359 (63.59%)
- **Citation**:
  - Yang, S. W., Chi, P. H., Chuang, Y. S., Lai, C. I. J., Lakhotia, K., Lin, Y. Y., ... & Lee, H. Y. (2021). SUPERB: Speech processing Universal PERformance Benchmark. *arXiv preprint arXiv:2105.01051*.
  - Hsu, W. N., Bolte, B., Tsai, Y. H. H., Lakhotia, K., Salakhutdinov, R., & Mohamed, A. (2021). HuBERT: Self-Supervised Speech Representation Learning by Masked Prediction of Hidden Units. *IEEE/ACM Transactions on Audio, Speech, and Language Processing*, 29, 3451-3460.

### Fine-tuned HuBERT Model
- **Model**: `BerkayPolat/hubert_ravdess_emotion`
- **Source**: Fine-tuned by project maintainer (BerkayPolat)
- **Base Model**: `superb/hubert-base-superb-er`
- **License**: Apache License 2.0 (inherited from base model)
- **URL**: https://huggingface.co/BerkayPolat/hubert_ravdess_emotion
- **Purpose**: Emotion classification (8 emotions: neutral, calm, happy, sad, angry, fearful, surprise, disgust)
- **Training Dataset**: RAVDESS (see Datasets section)
- **Training Strategy**: Frozen HuBERT layers, trained only classification head
- **Performance**: 60.00% accuracy on speaker-independent test set

---

## Datasets

### RAVDESS (Ryerson Audio-Visual Database of Emotional Speech and Song)
- **Dataset**: RAVDESS
- **Source**: Ryerson University
- **License**: Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)
- **URL**: https://zenodo.org/record/1188976
- **Purpose**: Training and evaluation of emotion recognition model
- **Citation**:
  - Livingstone, S. R., & Russo, F. A. (2018). The Ryerson Audio-Visual Database of Emotional Speech and Song (RAVDESS): A dynamic, multimodal set of facial and vocal expressions in North American English. *PLoS ONE*, 13(5), e0196391.
  - DOI: 10.1371/journal.pone.0196391
- **Dataset Details**:
  - 8 emotions: neutral, calm, happy, sad, angry, fearful, surprise, disgust
  - ~7,350 audio files from 24 actors (12 male, 12 female)
  - Audio-only modality used for training
  - Speaker-independent split: 16 actors train, 3 actors validation, 5 actors test

---

## AI-Generated Content

### Code Generation
Portions of this project's code were generated or assisted by AI tools, including but not limited to:

- **AI Assistant**: Cursor AI Agent / Claude (Anthropic)
- **Purpose**: Code generation, debugging and refactoring assistance
- **Scope**: 
  - Server actions and API handlers
  - Middleware (proxy.ts)
  - React components and UI implementation
  - Error handling and validation logic

### AI-Assisted Development
AI tools were used to assist with:

- Code refactoring and optimization
- Bug fixes and error resolution
- Type definitions and TypeScript annotations
- Test case generation
- Code review and suggestions
- Performance optimization recommendations

---

## Third-Party Services

### Supabase
- **Service**: Backend-as-a-Service (BaaS)
- **Provider**: Supabase, Inc.
- **URL**: https://supabase.com/
- **Usage**: 
  - Authentication (user sign-in/sign-up)
  - PostgreSQL database
  - File storage (audio files)
  - Real-time subscriptions
- **License**: Supabase is open-source (Apache License 2.0), but the hosted service is provided by Supabase, Inc.

### Hugging Face
- **Service**: Model hosting and distribution
- **Provider**: Hugging Face, Inc.
- **URL**: https://huggingface.co/
- **Usage**: 
  - Hosting fine-tuned HuBERT model
  - Model access via Hugging Face Hub
- **License**: Models are subject to their respective licenses (Apache License 2.0 for HuBERT)

---

## Contact

For questions about attributions or licensing, please contact the project maintainer:
- **Repository**: https://github.com/BerkayPolat-lab/mood.ai
- **Maintainer**: BerkayPolat

---

**Last Updated**: 2025-01-27

