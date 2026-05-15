import React from 'react';

export type CaptionItem = {
  text: string;
  startMs: number;
  endMs: number;
};

export const CaptionBar: React.FC<{
  currentMs: number;
  captions: CaptionItem[];
}> = ({currentMs, captions}) => {
  const current = captions.find(
    (c) => currentMs >= c.startMs && currentMs < c.endMs,
  );

  if (!current) {
    return null;
  }

  return (
    <div
      style={{
        position: 'absolute',
        left: '8%',
        right: '8%',
        bottom: 72,
        padding: '18px 28px',
        borderRadius: 18,
        backgroundColor: 'rgba(0,0,0,0.55)',
        color: 'white',
        fontSize: 42,
        fontWeight: 700,
        lineHeight: 1.35,
        textAlign: 'center',
      }}
    >
      {current.text}
    </div>
  );
};
